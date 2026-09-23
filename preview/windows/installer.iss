[Setup]
AppId={{B58B77D9-D5F5-4F5A-99A0-496F5EB3A412}
AppName=PackLab Studio Preview
AppVersion=0.1-preview
AppPublisher=PackLab
DefaultDirName={autopf}\PackLab Studio Preview
DefaultGroupName=PackLab Studio Preview
OutputDir=..\..\dist-installer
OutputBaseFilename=PackLabStudioPreviewSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\PackLabStudioPreview.exe

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
Source: "..\..\dist\PackLabStudioPreview.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\PackLab Studio Preview"; Filename: "{app}\PackLabStudioPreview.exe"; Tasks: desktopicon
Name: "{group}\PackLab Studio Preview"; Filename: "{app}\PackLabStudioPreview.exe"

[Run]
Filename: "{app}\PackLabStudioPreview.exe"; Description: "Launch PackLab Studio Preview"; Flags: nowait postinstall skipifsilent
