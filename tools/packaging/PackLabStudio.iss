#define MyAppName "PackLab Studio"
#define MyAppVersion GetEnv("PACKLAB_STUDIO_VERSION")
#define MyGitRevision GetEnv("PACKLAB_BUILD_REVISION")
#define MyStageDir StageDir
#define MyOutputDir OutputDir
#define MyOutputName OutputName

[Setup]
AppId={{B29FD9B3-3099-470F-A649-A0F5BB30E6A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PackLab
DefaultDirName={autopf}\PackLab Studio
DefaultGroupName=PackLab Studio
OutputDir={#MyOutputDir}
OutputBaseFilename={#MyOutputName}
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
VersionInfoDescription=PackLab Studio installer; source revision {#MyGitRevision}; unsigned

[Files]
Source: "{#MyStageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PackLab Studio"; Filename: "{app}\PackLabStudio.exe"
Name: "{autodesktop}\PackLab Studio"; Filename: "{app}\PackLabStudio.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\PackLabStudio.exe"; Description: "Launch PackLab Studio"; Flags: postinstall nowait skipifsilent
