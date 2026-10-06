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

[Code]
function HasSupportedVCRuntime: Boolean;
var
  Installed, Major, Minor, Build: Cardinal;
begin
  Result := False;
  if not RegQueryDWordValue(HKLM64,
    'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
    Exit;
  if (Installed <> 1) or
     not RegQueryDWordValue(HKLM64,
       'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Major', Major) or
     not RegQueryDWordValue(HKLM64,
       'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Minor', Minor) or
     not RegQueryDWordValue(HKLM64,
       'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Bld', Build) then
    Exit;
  Result := (Major > 14) or
    ((Major = 14) and ((Minor > 44) or ((Minor = 44) and (Build >= 35211))));
end;

function InitializeSetup: Boolean;
begin
  Result := HasSupportedVCRuntime;
  if not Result then
    MsgBox('PackLab Studio requires Microsoft Visual C++ 2015-2022 Redistributable (x64), version 14.44.35211 or later. Install or update the prerequisite from Microsoft, then run this installer again. PackLab does not download it automatically.', mbError, MB_OK);
end;
