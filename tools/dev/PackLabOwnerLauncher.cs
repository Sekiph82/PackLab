using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

internal static class PackLabOwnerLauncher
{
    private const string ExpectedSourceCommit = "__PACKLAB_SOURCE_COMMIT__";
    private const string RuntimeId = "__PACKLAB_RUNTIME_ID__";
    private const int StartupStabilitySeconds = 10;

    [STAThread]
    private static int Main()
    {
        string localAppData = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        string ownerRoot = Path.Combine(localAppData ?? String.Empty, "PackLab", "OwnerDev");
        string runtimeRoot = Path.Combine(ownerRoot, "releases", RuntimeId);
        string logRoot = Path.Combine(ownerRoot, "logs");
        string startupLog = Path.Combine(logRoot, "startup-" + DateTime.Now.ToString("yyyyMMdd-HHmmss-fff") + ".log");
        string deployedSha = "unknown";
        string studioVersion = "unknown";

        try
        {
            Directory.CreateDirectory(logRoot);
            string manifestPath = Path.Combine(runtimeRoot, "owner-dev-runtime.json");
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
                while (DateTime.UtcNow < deadline)
                {
                    if (child.WaitForExit(200))
                    {
                        int exitCode = child.ExitCode;
                        string childLog = File.Exists(startupLog) ? File.ReadAllText(startupLog, Encoding.UTF8) : "(no Python startup log was produced)";
                        string diagnostic = "PackLab OWNER DEV child exited during its startup stability window." + Environment.NewLine +
                            "timestamp_utc=" + DateTime.UtcNow.ToString("o") + Environment.NewLine +
                            "reason=early_child_exit" + Environment.NewLine +
                            "exit_code=" + exitCode + Environment.NewLine +
                            "deployed_sha=" + deployedSha + Environment.NewLine +
                            "studio_version=" + studioVersion + Environment.NewLine +
                            "python_startup_log=" + startupLog + Environment.NewLine + Environment.NewLine + childLog;
                        File.WriteAllText(startupLog, diagnostic + Environment.NewLine, new UTF8Encoding(false));
                        ShowStartupError("PackLab Studio exited during startup (code " + exitCode + "). Details: " + startupLog, startupLog, exitCode);
                        return 1;
                    }
                }
            }
            return 0;
        }
        catch (Exception error)
        {
            try
            {
                Directory.CreateDirectory(logRoot);
                File.WriteAllText(startupLog,
                    "PackLab OWNER DEV launcher failure." + Environment.NewLine +
                    "timestamp_utc=" + DateTime.UtcNow.ToString("o") + Environment.NewLine +
                    "reason=launcher_failure" + Environment.NewLine +
                    "deployed_sha=" + deployedSha + Environment.NewLine +
                    "studio_version=" + studioVersion + Environment.NewLine +
                    "exception_type=" + error.GetType().FullName + Environment.NewLine +
                    "exception_message=" + error.Message + Environment.NewLine,
                    new UTF8Encoding(false));
            }
            catch { }
            ShowStartupError("PackLab Studio could not start. Details: " + startupLog, startupLog, 1);
            return 1;
        }
    }

    private static void RequireFile(string path, string message)
    {
        if (!File.Exists(path)) throw new FileNotFoundException(message, path);
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
