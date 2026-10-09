using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

internal static class PackLabOwnerLauncher
{
    private const string ExpectedSourceCommit = "__PACKLAB_SOURCE_COMMIT__";
    private const string RuntimeId = "__PACKLAB_RUNTIME_ID__";
    private const string OwnerRoot = "__PACKLAB_OWNER_ROOT__";
    private const int StartupStabilitySeconds = 10;

    [STAThread]
    private static int Main()
    {
        string ownerRoot = ResolveOwnerRoot();
        string runtimeRoot = Path.Combine(ownerRoot, "current");
        string logRoot = Path.Combine(ownerRoot, "logs");
        string manifestPath = Path.Combine(runtimeRoot, "owner-dev-runtime.json");
        string startupLog = Path.Combine(logRoot, "startup-" + DateTime.Now.ToString("yyyyMMdd-HHmmss-fff") + ".log");
        string deployedSha = "unknown";
        string studioVersion = "unknown";

        try
        {
            Directory.CreateDirectory(logRoot);
            string pythonw = Path.Combine(runtimeRoot, ".venv", "Scripts", "pythonw.exe");
            string bootstrap = Path.Combine(runtimeRoot, "tools", "dev", "owner_packlab_bootstrap.py");
            RequireFile(manifestPath, "Owner runtime manifest is missing.");
            RequireFile(pythonw, "Owner runtime pythonw.exe is missing.");
            RequireFile(bootstrap, "Owner runtime bootstrap script is missing.");

            string manifest = File.ReadAllText(manifestPath, Encoding.UTF8);
            deployedSha = ReadManifestValue(manifest, "source_commit");
            studioVersion = ReadManifestValue(manifest, "studio_version");
            string manifestRuntimeId = ReadManifestValue(manifest, "runtime_id");
            string lockSha256 = ReadManifestValue(manifest, "uv_lock_sha256");
            string smokeStatus = ReadManifestValue(manifest, "smoke_status");
            string actualLockSha256;
            using (SHA256 sha256 = SHA256.Create())
            using (FileStream lockStream = File.OpenRead(Path.Combine(runtimeRoot, "uv.lock")))
                actualLockSha256 = BitConverter.ToString(sha256.ComputeHash(lockStream)).Replace("-", "").ToLowerInvariant();
            if (deployedSha != ExpectedSourceCommit || manifestRuntimeId != RuntimeId ||
                !Regex.IsMatch(deployedSha, "^[0-9a-f]{40}$") ||
                !Regex.IsMatch(lockSha256, "^[0-9a-f]{64}$") || actualLockSha256 != lockSha256 ||
                smokeStatus != "PASS")
                throw new InvalidDataException("Owner runtime manifest is invalid or has no successful smoke result.");
            if (!Regex.IsMatch(studioVersion, "^\\d+\\.\\d+\\.\\d+"))
                throw new InvalidDataException("Owner runtime manifest has an invalid Studio version.");

            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = pythonw;
            start.Arguments = QuoteArgument(bootstrap);
            start.WorkingDirectory = runtimeRoot;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.WindowStyle = ProcessWindowStyle.Hidden;
            start.EnvironmentVariables["PACKLAB_OWNERDEV_DIAGNOSTICS"] = "1";
            start.EnvironmentVariables["PACKLAB_OWNERDEV_STARTUP_LOG"] = startupLog;
            start.EnvironmentVariables["PACKLAB_OWNERDEV_SOURCE_SHA"] = deployedSha;
            start.EnvironmentVariables["PACKLAB_OWNERDEV_STUDIO_VERSION"] = studioVersion;
            start.EnvironmentVariables["PACKLAB_OWNERDEV_RUNTIME_ID"] = RuntimeId;

            using (Process child = Process.Start(start))
            {
                if (child == null) throw new InvalidOperationException("Windows did not create the PackLab runtime process.");
                DateTime deadline = DateTime.UtcNow.AddSeconds(StartupStabilitySeconds);
                DateTime nextDescendantLookup = DateTime.MinValue;
                int studioProcessId = 0;
                while (DateTime.UtcNow < deadline)
                {
                    if (child.WaitForExit(200))
                    {
                        int exitCode = child.ExitCode;
                        if (exitCode != 0)
                            return ReportEarlyChildExit(startupLog, deployedSha, studioVersion, exitCode,
                                "The OWNER DEV Python launcher exited with a nonzero code.");

                        if (studioProcessId == 0 && DateTime.UtcNow >= nextDescendantLookup)
                        {
                            studioProcessId = FindVisibleStudioDescendant(child.Id);
                            nextDescendantLookup = DateTime.UtcNow.AddMilliseconds(500);
                        }

                        if (studioProcessId != 0 && !HasVisibleStudioWindow(studioProcessId))
                            return ReportEarlyChildExit(startupLog, deployedSha, studioVersion, exitCode,
                                "The launched PackLab Studio window exited or became hidden during startup.");
                    }
                }

                if (child.HasExited && studioProcessId == 0)
                    return ReportEarlyChildExit(startupLog, deployedSha, studioVersion, child.ExitCode,
                        "The Python launcher exited without leaving a visible PackLab Studio window.");
            }
            return 0;
        }
        catch (Exception error)
        {
            try
            {
                FileNotFoundException missingFile = error as FileNotFoundException;
                Directory.CreateDirectory(logRoot);
                File.WriteAllText(startupLog,
                    "PackLab OWNER DEV launcher failure." + Environment.NewLine +
                    "timestamp_utc=" + DateTime.UtcNow.ToString("o") + Environment.NewLine +
                    "reason=launcher_failure" + Environment.NewLine +
                    "deployed_sha=" + deployedSha + Environment.NewLine +
                    "studio_version=" + studioVersion + Environment.NewLine +
                    "owner_root=" + ownerRoot + Environment.NewLine +
                    "runtime_root=" + runtimeRoot + Environment.NewLine +
                    "manifest_path=" + manifestPath + Environment.NewLine +
                    "exception_type=" + error.GetType().FullName + Environment.NewLine +
                    "exception_path=" + (missingFile == null ? String.Empty : missingFile.FileName) + Environment.NewLine +
                    "exception_message=" + error.Message + Environment.NewLine,
                    new UTF8Encoding(false));
            }
            catch { }
            ShowStartupError("PackLab Studio could not start. Details: " + startupLog, startupLog, 1);
            return 1;
        }
    }

    private static string ResolveOwnerRoot()
    {
        string executablePath = Process.GetCurrentProcess().MainModule.FileName;
        string executableDirectory = Path.GetDirectoryName(executablePath);
        string directoryName = new DirectoryInfo(executableDirectory).Name;

        // The stable launcher inside OwnerDev\launcher resolves its owner root
        // from that layout. The Desktop copy resolves the project-local runtime
        // beside it, so a previously embedded AppData path cannot win.
        if (String.Equals(directoryName, "launcher", StringComparison.OrdinalIgnoreCase))
            return Directory.GetParent(executableDirectory).FullName;

        string desktopOwnerRoot = Path.Combine(executableDirectory, "PackLab", "OwnerDev");
        if (Directory.Exists(desktopOwnerRoot)) return desktopOwnerRoot;

        // Keep the compiled owner root for isolated launcher contract fixtures
        // and non-Desktop deployments that do not use the Desktop project layout.
        return OwnerRoot;
    }

    private static void RequireFile(string path, string message)
    {
        if (!File.Exists(path)) throw new FileNotFoundException(message, path);
    }

    private static int FindVisibleStudioDescendant(int rootProcessId)
    {
        Dictionary<int, int> parentByProcessId = new Dictionary<int, int>();
        using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(
            "SELECT ProcessId, ParentProcessId FROM Win32_Process"))
        using (ManagementObjectCollection processes = searcher.Get())
        {
            foreach (ManagementObject process in processes)
            using (process)
            {
                int processId = Convert.ToInt32(process["ProcessId"]);
                int parentProcessId = Convert.ToInt32(process["ParentProcessId"]);
                parentByProcessId[processId] = parentProcessId;
            }
        }

        HashSet<int> descendants = new HashSet<int> { rootProcessId };
        bool changed;
        do
        {
            changed = false;
            foreach (KeyValuePair<int, int> entry in parentByProcessId)
                if (descendants.Contains(entry.Value) && descendants.Add(entry.Key)) changed = true;
        } while (changed);

        foreach (Process process in Process.GetProcesses())
        using (process)
            if (descendants.Contains(process.Id) && HasVisibleStudioWindow(process.Id)) return process.Id;
        return 0;
    }

    private static bool HasVisibleStudioWindow(int processId)
    {
        try
        {
            using (Process process = Process.GetProcessById(processId))
                return process.MainWindowHandle != IntPtr.Zero && process.MainWindowTitle == "PackLab Studio";
        }
        catch (ArgumentException) { return false; }
        catch (InvalidOperationException) { return false; }
    }

    private static int ReportEarlyChildExit(string startupLog, string deployedSha, string studioVersion,
        int exitCode, string detail)
    {
        string childLog = File.Exists(startupLog) ? File.ReadAllText(startupLog, Encoding.UTF8) : "(no Python startup log was produced)";
        string diagnostic = "PackLab OWNER DEV child exited during its startup stability window." + Environment.NewLine +
            "timestamp_utc=" + DateTime.UtcNow.ToString("o") + Environment.NewLine +
            "reason=early_child_exit" + Environment.NewLine +
            "exit_code=" + exitCode + Environment.NewLine +
            "deployed_sha=" + deployedSha + Environment.NewLine +
            "studio_version=" + studioVersion + Environment.NewLine +
            "python_startup_log=" + startupLog + Environment.NewLine +
            "exception_message=" + detail + Environment.NewLine + Environment.NewLine + childLog;
        File.WriteAllText(startupLog, diagnostic + Environment.NewLine, new UTF8Encoding(false));
        ShowStartupError("PackLab Studio exited during startup (code " + exitCode + "). Details: " + startupLog, startupLog, exitCode);
        return 1;
    }

    private static string ReadManifestValue(string json, string name)
    {
        Match match = Regex.Match(json, "\"" + Regex.Escape(name) + "\"\\s*:\\s*\"([^\"]*)\"");
        if (!match.Success) throw new InvalidDataException("Owner runtime manifest is missing " + name + ".");
        return match.Groups[1].Value;
    }

    private static string QuoteArgument(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    private static void ShowStartupError(string message, string logPath, int exitCode)
    {
#if OWNERDEV_TEST
        string resultPath = Environment.GetEnvironmentVariable("PACKLAB_OWNERDEV_TEST_RESULT");
        if (!String.IsNullOrEmpty(resultPath))
            File.WriteAllText(resultPath, "dialog_shown=true" + Environment.NewLine + "exit_code=" + exitCode + Environment.NewLine + "log=" + logPath);
#else
        MessageBox.Show(message, "PackLab Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
#endif
    }
}
