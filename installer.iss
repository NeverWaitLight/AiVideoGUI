; AI Video GUI 安装脚本

#define MyAppName "AI Video GUI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "WaitLight"
#define MyAppURL "https://github.com/yourusername/ai-video-gui"
#define MyAppExeName "AI-Video-GUI.exe"

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
OutputBaseFilename=AI-Video-GUI-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes

; 权限和架构
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; UI 配置
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 复制整个打包目录到安装目录
Source: "dist\AI-Video-GUI\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AI-Video-GUI\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; 安装时直接复制 resources 到工作目录（避免首次运行时复制）
Source: "dist\AI-Video-GUI\_internal\resources\*"; DestDir: "{localappdata}\ai-video-gui\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; 桌面快捷方式（可选）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行程序（可选）
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
