; Instalador oficial do VOID//SHIFT (Inno Setup 6)
#define AppVersion "1.0.0"

[Setup]
AppId={{B74AE7B0-9A9F-4C93-9A30-0D51F7C91000}
AppName=VOID//SHIFT
AppVersion={#AppVersion}
AppPublisher=VOID//SHIFT
DefaultDirName={localappdata}\Programs\VOID-SHIFT
DefaultGroupName=VOID//SHIFT
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=VOID-SHIFT-Setup
SetupIconFile=..\assets\windows\void-shift.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\VOID-SHIFT.exe

[Files]
Source: "..\dist\VOID-SHIFT.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\VOID//SHIFT"; Filename: "{app}\VOID-SHIFT.exe"
Name: "{autodesktop}\VOID//SHIFT"; Filename: "{app}\VOID-SHIFT.exe"

[Run]
Filename: "{app}\VOID-SHIFT.exe"; Description: "Executar VOID//SHIFT"; Flags: postinstall nowait skipifsilent
