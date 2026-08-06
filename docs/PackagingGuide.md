# Windows 安装程序打包指南

本文档记录如何将 AI Video GUI 项目打包为 Windows 安装程序（.exe）。

## 方案概述

**打包工具链：**
- **PyInstaller** - 将 Python 应用打包为可执行文件
- **Inno Setup** - 创建 Windows 安装程序

**关键特性：**
- 单文件或单目录 exe 分发
- 自动包含 PySide6/Qt 依赖
- resources 目录在首次运行时自动复制到工作目录
- 生成标准的 Windows 安装向导

## 步骤 1：安装打包工具

### 1.1 安装 PyInstaller

```bash
# 使用 uv 添加 PyInstaller 到开发依赖
uv add --dev pyinstaller
```

### 1.2 安装 Inno Setup

1. 下载 [Inno Setup](https://jrsoftware.org/isdl.php)（免费开源）
2. 运行安装程序（默认安装到 `C:\Program Files (x86)\Inno Setup 6`）

## 步骤 2：创建 PyInstaller 配置文件

在项目根目录创建 `ai-video-gui.spec` 文件：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('qml', 'qml'),                    # 包含 QML 文件
        ('resources', 'resources'),        # 包含资源文件（样式图、封面等）
        ('prompts/templates', 'prompts/templates'),  # 包含提示词模板
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'sqlalchemy.ext.baked',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI-Video-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',  # 如果有应用图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI-Video-GUI',
)
```

**关键配置说明：**
- `datas` - 指定需要打包的非 Python 文件（QML、资源、模板）
- `hiddenimports` - 显式声明动态导入的模块（避免打包遗漏）
- `console=False` - 打包为 GUI 应用（不显示黑色控制台窗口）
- `exclude_binaries=True` - 生成单目录模式（exe + _internal 文件夹）

## 步骤 3：打包可执行文件

```bash
# 清理之前的构建产物
rm -rf build dist

# 使用 spec 文件打包
uv run pyinstaller ai-video-gui.spec

# 打包完成后，产物位于 dist/AI-Video-GUI/
# 目录结构：
# dist/AI-Video-GUI/
# ├── AI-Video-GUI.exe          # 主程序
# ├── _internal/                # 依赖库和资源
# │   ├── qml/                  # QML 文件
# │   ├── resources/            # 资源文件
# │   ├── prompts/              # 提示词模板
# │   └── ... (其他依赖)
```

## 步骤 4：测试打包结果

在打包机器上测试：

```bash
# 运行打包后的程序
./dist/AI-Video-GUI/AI-Video-GUI.exe
```

**验证要点：**
1. 程序能正常启动，无缺失 DLL 错误
2. QML 界面正常显示
3. resources 目录自动复制到 `%LOCALAPPDATA%\ai-video-gui\resources\`
4. 视频生成、素材库等功能正常

## 步骤 5：创建安装程序（Inno Setup）

在项目根目录创建 `installer.iss` 文件：

```iss
; AI Video GUI 安装脚本

#define MyAppName "AI Video GUI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://yourwebsite.com"
#define MyAppExeName "AI-Video-GUI.exe"

[Setup]
; 应用信息
AppId={{YOUR-GUID-HERE}}
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
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; UI 配置
WizardStyle=modern
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt  ; 如果有许可证文件
; InfoBeforeFile=README.txt  ; 如果需要安装前说明

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
```

**生成安装程序：**

```bash
# 方法 1：使用 Inno Setup GUI
# 1. 打开 Inno Setup Compiler
# 2. File -> Open -> 选择 installer.iss
# 3. Build -> Compile

# 方法 2：命令行编译
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# 安装程序生成在 output/AI-Video-GUI-Setup-1.0.0.exe
```

## resources 目录自动复制机制

**当前实现（已有代码）：**

项目已在 `utils/resources.py` 中实现 `copy_resources_to_workspace()` 函数，在 `main.py` 启动时自动调用：

```python
# main.py
from utils.resources import copy_resources_to_workspace

def main():
    # 应用启动时自动复制资源文件到工作目录
    copy_resources_to_workspace()
    # ... 其他初始化代码
```

**工作原理：**
1. PyInstaller 将 `resources/` 打包到 `dist/AI-Video-GUI/_internal/resources/`
2. 用户首次运行程序时，`copy_resources_to_workspace()` 检测工作目录 `%LOCALAPPDATA%\ai-video-gui\resources\`
3. 如果不存在或文件过期，自动从安装目录复制（基于文件修改时间的增量更新）
4. 后续运行时，仅更新有变化的文件

**无需额外配置**，打包后的程序会自动处理资源复制。

## 完整打包流程（快速参考）

```bash
# 1. 安装打包工具
uv add --dev pyinstaller

# 2. 创建 spec 文件（见步骤 2）
# 编辑 ai-video-gui.spec

# 3. 打包可执行文件
uv run pyinstaller ai-video-gui.spec

# 4. 测试打包结果
./dist/AI-Video-GUI/AI-Video-GUI.exe

# 5. 创建 Inno Setup 脚本（见步骤 5）
# 编辑 installer.iss

# 6. 生成安装程序
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# 7. 分发安装程序
# output/AI-Video-GUI-Setup-1.0.0.exe
```

## 常见问题

### 1. 打包后程序启动报错 "Failed to load QML"

**原因：** QML 文件未正确打包

**解决：** 检查 spec 文件中的 `datas` 配置，确保 `('qml', 'qml')` 存在

### 2. 打包后资源文件缺失

**原因：** resources 目录未打包，或路径错误

**解决：** 
- 检查 spec 文件中的 `datas` 配置
- 确保 `utils/resources.py` 中的路径解析逻辑正确

### 3. 控制台窗口闪烁

**原因：** spec 文件中 `console=True`

**解决：** 修改为 `console=False`

### 4. 程序体积过大

**优化方案：**
- 使用 `upx=True` 压缩二进制文件
- 在 spec 文件中 `excludes` 排除不需要的模块
- 考虑使用 Nuitka（编译为 C++）进一步优化

### 5. 杀毒软件误报

**原因：** PyInstaller 打包的 exe 常被误报为病毒

**解决：**
- 使用代码签名证书签名 exe 文件
- 向杀毒软件厂商提交白名单申请
- 在 README 中说明情况

## 进阶选项

### 单文件模式（可选）

如果希望打包为单个 exe 文件（不含 _internal 文件夹），修改 spec 文件：

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # 添加
    a.zipfiles,      # 添加
    a.datas,         # 添加
    [],
    name='AI-Video-GUI',
    # ... 其他配置
    onefile=True,    # 添加此行
)
```

**注意：** 单文件模式启动较慢（需解压临时文件），不推荐用于大型应用。

### 添加应用图标

1. 准备 `.ico` 格式图标文件（建议 256x256）
2. 放置到 `resources/icon.ico`
3. 在 spec 文件中设置 `icon='resources/icon.ico'`

### 代码签名（消除 Windows 警告）

**问题：Windows SmartScreen 警告 "Windows 已保护你的电脑"**

未签名的安装程序会被 Windows Defender SmartScreen 拦截，显示警告并阻止运行。

**解决方案：购买代码签名证书对程序签名**

#### 方案 1：EV 代码签名证书（推荐，立即生效）

**特点：**
- **立即消除警告** - 签名后立即获得 SmartScreen 信任
- **最高信任级别** - Extended Validation 证书经过严格身份验证
- **价格较高** - $300-500/年
- **需要硬件 Token** - 证书存储在 USB 硬件设备中，无法导出

**购买渠道：**
- [DigiCert](https://www.digicert.com/signing/code-signing-certificates) - EV Code Signing Certificate
- [Sectigo](https://sectigostore.com/code-signing/ev-code-signing-certificate) - EV Code Signing
- [GlobalSign](https://www.globalsign.com/en/code-signing-certificate/ev-code-signing) - EV Code Signing

**购买流程：**
1. 选择 EV Code Signing Certificate
2. 提交公司资质文件（营业执照、法人身份证等）
3. 等待 CA 审核（3-7 个工作日）
4. 收到 USB Token 硬件设备（内含证书）
5. 安装 SafeNet 或 Gemalto 驱动程序

**签名命令：**

```bash
# 使用 signtool（Windows SDK 自带）
# USB Token 插入电脑后自动识别证书

signtool sign /n "Your Company Name" /t http://timestamp.digicert.com /fd SHA256 /v dist/AI-Video-GUI/AI-Video-GUI.exe

# 对安装程序也签名
signtool sign /n "Your Company Name" /t http://timestamp.digicert.com /fd SHA256 /v output/AI-Video-GUI-Setup-1.0.0.exe
```

#### 方案 2：普通 OV 代码签名证书（经济，需等待信誉积累）

**特点：**
- **初期仍有警告** - 签名后仍需 2-8 周积累 SmartScreen 信誉
- **需要信誉积累** - 足够的下载量 + 时间 + 无恶意行为报告
- **价格较低** - $100-200/年
- **可导出** - 证书为 .pfx 文件，可备份

**购买渠道：**
- [Sectigo](https://sectigostore.com/code-signing) - Code Signing Certificate
- [DigiCert](https://www.digicert.com/signing/code-signing-certificates) - Standard Code Signing
- [Certum](https://en.sklep.certum.pl/code-signing-certificates.html) - Open Source Code Signing（$86/年，支持个人开发者）

**签名命令：**

```bash
# 使用 .pfx 证书文件签名
signtool sign /f "path\to\certificate.pfx" /p "password" /t http://timestamp.digicert.com /fd SHA256 /v dist/AI-Video-GUI/AI-Video-GUI.exe

# 对安装程序也签名
signtool sign /f "path\to\certificate.pfx" /p "password" /t http://timestamp.digicert.com /fd SHA256 /v output/AI-Video-GUI-Setup-1.0.0.exe
```

**加速信誉积累方法：**
- 在官网提供下载（使用 HTTPS）
- 鼓励用户通过官方渠道下载
- 保持程序行为稳定，避免触发安全软件警报
- 定期更新但保持同一个证书签名

#### 方案 3：临时方案（不推荐，用户体验差）

如果暂时无法购买证书，可以在文档中告知用户如何绕过警告：

**README.md 或官网说明：**

```markdown
## Windows SmartScreen 警告处理

由于程序尚未积累足够的下载量，Windows 可能显示 SmartScreen 警告。这是正常现象，程序本身安全无害。

**解除方法：**
1. 点击警告窗口中的 "更多信息"
2. 点击 "仍要运行" 按钮
3. 程序即可正常安装

我们正在申请代码签名证书，后续版本将消除此警告。
```

#### 签名工具安装

**安装 Windows SDK（包含 signtool）：**

```bash
# 下载 Windows SDK
# https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/

# 或仅安装 signtool（使用 Chocolatey）
choco install windows-sdk-10-version-2004-all

# signtool 默认路径
C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\signtool.exe
```

#### 验证签名

签名完成后，验证签名是否有效：

```bash
# 查看签名信息
signtool verify /pa /v dist/AI-Video-GUI/AI-Video-GUI.exe

# 输出应包含：
# - 签名者名称
# - 证书有效期
# - 时间戳服务器
# - "Successfully verified" 字样
```

**在 Windows 资源管理器中验证：**
1. 右键点击 exe 文件 → 属性
2. 切换到 "数字签名" 标签页
3. 应显示签名者信息和证书详情

#### 成本对比

| 方案 | 年费用 | 立即消除警告 | 适用场景 |
|------|--------|-------------|---------|
| **EV 证书** | $300-500 | ✅ 是 | 商业产品、企业用户 |
| **OV 证书** | $100-200 | ❌ 需等待 | 个人开发者、小团队 |
| **不签名** | $0 | ❌ 一直警告 | 开源项目、内部工具 |

#### 推荐策略

**个人开发者/开源项目：**
- 初期：使用临时方案（README 说明 + 用户手动绕过）
- 后期：购买 Certum Open Source Code Signing（$86/年）

**商业产品：**
- 直接购买 EV 证书（用户体验最佳）
- 同时申请 Microsoft Store 分发（Store 内下载无需证书）

**企业内部工具：**
- 使用企业自有证书签名
- 或在域内通过 GPO 策略信任自签名证书

## 参考资料

- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)
- [Inno Setup 官方文档](https://jrsoftware.org/ishelp/)
- [PySide6 打包指南](https://doc.qt.io/qtforpython-6/deployment.html)
