; Script de Instalação Inno Setup para o BiblioTEC (Windows)
; Gera um instalador profissional .exe: BiblioTEC_Setup_v1.0.0_Windows_x64.exe

#define MyAppName "BiblioTEC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BiblioTEC Open Source Community"
#define MyAppURL "https://github.com/dcprj/bibliotec"
#define MyAppExeName "BiblioTEC.exe"

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
OutputBaseFilename=BiblioTEC_Setup_v{#MyAppVersion}_Windows_x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiar todo o conteúdo gerado pelo PyInstaller em dist/BiblioTEC
Source: "..\dist\BiblioTEC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
