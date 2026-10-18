; Instalador oficial do INCARNATE (Inno Setup 6)
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#ifndef AppVersionInfo
  #define AppVersionInfo "0.0.0.0"
#endif

[Setup]
AppId={{B74AE7B0-9A9F-4C93-9A30-0D51F7C91000}
AppName=INCARNATE
AppVersion={#AppVersion}
AppPublisher=INCARNATE
DefaultDirName={localappdata}\Programs\INCARNATE
DefaultGroupName=INCARNATE
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=INCARNATE-Setup
SetupIconFile=..\assets\windows\void-shift.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion={#AppVersionInfo}
UninstallDisplayIcon={app}\INCARNATE.exe

[InstallDelete]
; Remove the old executable and shortcuts from an in-place upgrade.
Type: files; Name: "{app}\VOID-SHIFT.exe"
Type: files; Name: "{autoprograms}\VOID\SHIFT.lnk"
Type: files; Name: "{autodesktop}\VOID\SHIFT.lnk"

[Files]
Source: "..\dist\INCARNATE.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\INCARNATE"; Filename: "{app}\INCARNATE.exe"
Name: "{autodesktop}\INCARNATE"; Filename: "{app}\INCARNATE.exe"

[Run]
Filename: "{app}\INCARNATE.exe"; Description: "Executar INCARNATE"; Flags: postinstall nowait skipifsilent
