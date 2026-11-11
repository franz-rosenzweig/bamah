; Bamah for Windows: an installer for one person, which needs no administrator. It copies what
; dotnet publish made (build\Bamah) to %LOCALAPPDATA%\Programs\Bamah and puts Bamah in the Start
; menu. The Windows workflow makes it:
;
;   iscc /DVersion=0.1.0 /DSource=build\Bamah windows\installer.iss
;
; Uninstalling leaves the settings and the sign-in in %LOCALAPPDATA%\Bamah.

#ifndef Version
  #define Version "0.0.0"
#endif
#ifndef Source
  #define Source "..\build\Bamah"
#endif

[Setup]
AppId={{B7A1C9E4-3F2D-4B8A-9C61-5E0D2A7F4B19}
AppName=Bamah
AppVersion={#Version}
AppVerName=Bamah {#Version}
AppPublisher=franz-rosenzweig
AppPublisherURL=https://github.com/franz-rosenzweig/bamah
AppSupportURL=https://docs.tiresia.xyz/bamah/
DefaultDirName={localappdata}\Programs\Bamah
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\build\out
OutputBaseFilename=Bamah-{#Version}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#Source}\Assets\Bamah.ico
UninstallDisplayIcon={app}\Bamah.exe
UninstallDisplayName=Bamah
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Source}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Bamah"; Filename: "{app}\Bamah.exe"
Name: "{autodesktop}\Bamah"; Filename: "{app}\Bamah.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Bamah.exe"; Description: "{cm:LaunchProgram,Bamah}"; Flags: nowait postinstall skipifsilent
