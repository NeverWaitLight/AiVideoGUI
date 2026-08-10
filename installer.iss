; AI Video GUI 安装脚本

#define MyAppName "AiVideoGUI"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "WaitLight"
#define MyAppURL "https://github.com/yourusername/ai-video-gui"
#define MyAppExeName "AiVideoGUI.exe"

[Setup]
; 应用信息
AppId={{8F3A5B2C-9D4E-4A1F-B6C7-E8D9F0A1B2C3}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; 安装路径
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; 输出配置
OutputDir=output
OutputBaseFilename=AiVideoGUI-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes

; 权限和架�?
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; UI 配置
WizardStyle=modern
DisableProgramGroupPage=yes
SetupIconFile=resources\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 复制整个打包目录到安装目�?
Source: "dist\AiVideoGUI\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AiVideoGUI\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; 安装时直接复�?resources 到工作目录（避免首次运行时复制）
Source: "dist\AiVideoGUI\_internal\resources\*"; DestDir: "{localappdata}\ai-video-gui\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单快捷方�?
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; 桌面快捷方式（可选）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行程序（可选）
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
