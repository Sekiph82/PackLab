Add-Type -Name W -Namespace U -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int c); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);'
$p = Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like 'PackLab Studio*' } | Select-Object -First 1
if ($p) { [U.W]::ShowWindow($p.MainWindowHandle, 3) | Out-Null; [U.W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; "front $($p.Id) $($p.MainWindowTitle)" } else { 'no packlab window' }
