; Script de Instalação Inno Setup para o Tomus (Windows)
; Gera um instalador profissional .exe: Tomus_Setup_v1.1.0_Windows_x64.exe

#define MyAppName "Tomus"
#ifndef MyAppVersion
#define MyAppVersion "1.1.1"
#endif
#define MyAppPublisher "Tomus Open Source Community"
#define MyAppURL "https://github.com/dcprj/tomus"
#define MyAppExeName "Tomus.exe"

[Setup]
AppId={{D37E6F10-B14C-409D-A3D9-974F8175E7B1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Tomus_Setup_v{#MyAppVersion}_Windows_x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
SetupIconFile=icons\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiar todo o conteúdo gerado pelo PyInstaller em dist/Tomus
Source: "..\dist\Tomus\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
