# Windows 平台打包方案

## 1. 方案概述

本文档详细介绍如何将 AI Video GUI 项目打包为 Windows 平台的独立安装包。

### 1.1 打包目标

- 生成独立的 `.exe` 可执行文件（包含所有依赖）
- 制作标准的 Windows 安装程序（带卸载功能）
- 支持自动创建开始菜单快捷方式和桌面图标
- 文件大小控制在 200MB 以内

### 1.2 项目特点分析

- **Python 版本**: 3.11-3.12
- **GUI 框架**: PySide6 + Qt Quick (QML)
- **资源管理**: Qt Resource System (`.qrc` → `resources_rc.py`)
- **数据库**: SQLite (嵌入式，无需额外安装)
- **外部依赖**: ffmpeg（通过 `imageio-ffmpeg` 自动管理）
- **数据目录**: `%LOCALAPPDATA%\ai-video-gui\`

## 2. 打包工具选型

### 2.1 可选方案对比

| 工具 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **PyInstaller** | 成熟稳定，社区活跃，PySide6 支持好 | 打包体积较大 | ⭐⭐⭐⭐⭐ |
| **Nuitka** | 编译为 C++，性能好，体积小 | 配置复杂，Qt 支持不完善 | ⭐⭐⭐ |
| **cx_Freeze** | 跨平台，配置简单 | PySide6 支持一般 | ⭐⭐⭐ |
| **py2exe** | Windows 原生 | 已停止维护，不支持 Python 3.11+ | ⭐ |

### 2.2 推荐方案：PyInstaller + Inno Setup

**理由**：
1. PyInstaller 对 PySide6/QML 支持最成熟
2. 社区活跃，问题容易找到解决方案
3. 自动处理依赖，配置相对简单
4. Inno Setup 是业界标准的 Windows 安装程序制作工具

## 3. PyInstaller 打包方案

### 3.1 安装 PyInstaller

```bash
# 使用 uv 安装到开发依赖
uv add --dev pyinstaller
```

### 3.2 创建 PyInstaller 配置文件

在项目根目录创建 `ai-video-gui.spec` 文件：

```python
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 收集所有 QML 文件
qml_files = []
for root, dirs, files in os.walk(ROOT_DIR / "qml"):
    for file in files:
        if file.endswith(".qml"):
            src = os.path.join(root, file)
            dest = os.path.relpath(root, ROOT_DIR)
            qml_files.append((src, dest))

# 收集资源文件（图标、封面等）
resource_files = []
for root, dirs, files in os.walk(ROOT_DIR / "resources"):
    for file in files:
        src = os.path.join(root, file)
        dest = os.path.relpath(root, ROOT_DIR)
        resource_files.append((src, dest))

# 收集 prompts 模板文件
prompt_files = []
for root, dirs, files in os.walk(ROOT_DIR / "prompts" / "templates"):
    for file in files:
        if file.endswith(".yaml"):
            src = os.path.join(root, file)
            dest = os.path.relpath(root, ROOT_DIR)
            prompt_files.append((src, dest))

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        *qml_files,
        *resource_files,
        *prompt_files,
        ('resources.qrc', '.'),  # Qt Resource 配置文件
    ],
    hiddenimports=[
        # PySide6 核心模块
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        
        # SQLAlchemy
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.declarative',
        
        # 日志
        'loguru',
        
        # 依赖注入
        'dependency_injector',
        
        # 项目模块
        'bridge',
        'config',
        'di',
        'models',
        'prompts',
        'providers',
        'service',
        'storage',
        'utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除测试模块
        'tests',
        'pytest',
        'unittest',
        
        # 排除不必要的 Qt 模块
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3D',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        
        # 排除开发工具
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ai-video-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩（需要安装 UPX）
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo.ico',  # 应用图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ai-video-gui',
)
```

### 3.3 打包命令

```bash
# 方式 1：使用 .spec 配置文件（推荐）
uv run pyinstaller ai-video-gui.spec --clean

# 方式 2：直接命令行打包（首次使用，会自动生成 .spec 文件）
uv run pyinstaller main.py \
  --name="ai-video-gui" \
  --icon="resources/logo.ico" \
  --windowed \
  --add-data="qml:qml" \
  --add-data="resources:resources" \
  --add-data="prompts/templates:prompts/templates" \
  --hidden-import="PySide6.QtCore" \
  --hidden-import="PySide6.QtQml" \
  --hidden-import="PySide6.QtQuick" \
  --clean
```

### 3.4 打包输出

```
dist/
└── ai-video-gui/
    ├── ai-video-gui.exe       # 主程序
    ├── qml/                   # QML 文件
    ├── resources/             # 资源文件
    ├── prompts/               # 提示词模板
    ├── _internal/             # 依赖库和运行时文件
    │   ├── PySide6/
    │   ├── Qt6/
    │   ├── imageio_ffmpeg/
    │   └── ...
    └── ...
```

## 4. 制作 Windows 安装程序

### 4.1 安装 Inno Setup

下载并安装 [Inno Setup](https://jrsoftware.org/isdl.php)（免费开源）

### 4.2 创建 Inno Setup 脚本

在项目根目录创建 `installer.iss` 文件：

```ini
; Inno Setup 安装脚本

#define MyAppName "AI Video GUI"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/yourusername/ai-video-gui"
#define MyAppExeName "ai-video-gui.exe"

[Setup]
; 应用程序基本信息
AppId={{B4F3C8D2-7A5E-4F9B-8D6C-1E2F3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; 安装程序图标
SetupIconFile=resources\logo.ico
; 输出设置
OutputDir=output
OutputBaseFilename=ai-video-gui-setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; Windows 版本要求
MinVersion=10.0.17763
; 架构
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; 权限
PrivilegesRequired=lowest
; 许可协议（如有）
; LicenseFile=LICENSE.txt
; 禁用欢迎页面
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 所有打包文件
Source: "dist\ai-video-gui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行程序
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除用户数据（可选，谨慎使用）
; Type: filesandordirs; Name: "{localappdata}\ai-video-gui"
```

### 4.3 生成安装程序

```bash
# 1. 先用 PyInstaller 打包
uv run pyinstaller ai-video-gui.spec --clean

# 2. 使用 Inno Setup 编译安装程序
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# 输出文件：output/ai-video-gui-setup-0.1.0.exe
```

## 5. 常见问题和解决方案

### 5.1 QML 文件未打包

**问题**：运行时报错 "Cannot find QML file"

**解决方案**：
1. 确保 `.spec` 文件中包含 QML 文件收集逻辑
2. 检查 `main.py` 中的 QML 路径加载方式：
   ```python
   # 错误：绝对路径在打包后失效
   qml_dir = os.path.join(os.path.dirname(__file__), "qml")
   
   # 正确：使用 sys._MEIPASS（PyInstaller 临时目录）
   if getattr(sys, 'frozen', False):
       # 打包后运行
       base_path = sys._MEIPASS
   else:
       # 开发环境
       base_path = os.path.dirname(__file__)
   qml_dir = os.path.join(base_path, "qml")
   ```

### 5.2 Qt 插件缺失

**问题**：运行时报错 "Could not find Qt platform plugin 'windows'"

**解决方案**：
在 `.spec` 文件中添加 Qt 插件：
```python
# 在 Analysis 中添加
binaries=[
    (r'C:\path\to\python\Lib\site-packages\PySide6\plugins\platforms\*', 'PySide6/plugins/platforms'),
],
```

### 5.3 ffmpeg 缺失

**问题**：视频元数据提取失败

**解决方案**：
`imageio-ffmpeg` 会自动打包 ffmpeg 二进制文件，但需确保在 `hiddenimports` 中包含：
```python
hiddenimports=[
    'imageio_ffmpeg',
],
```

### 5.4 打包体积过大

**问题**：`dist/` 目录超过 500MB

**优化方案**：
1. **启用 UPX 压缩**（已在 `.spec` 中配置）
   ```bash
   # 下载 UPX: https://github.com/upx/upx/releases
   # 解压到 PATH 环境变量路径
   ```

2. **排除不必要的 Qt 模块**（已在 `.spec` 的 `excludes` 中配置）

3. **使用单文件模式**（不推荐，启动慢）：
   ```python
   exe = EXE(
       ...,
       a.binaries,  # 将此行移到 EXE 内部
       a.zipfiles,  # 将此行移到 EXE 内部
       a.datas,     # 将此行移到 EXE 内部
       ...,
       onefile=True,  # 启用单文件模式
   )
   ```

### 5.5 运行时路径问题

**问题**：配置文件、数据库找不到

**解决方案**：
所有用户数据都放在固定的用户目录，不依赖应用安装路径：
```python
# 正确做法（已在 utils/paths.py 中实现）
workspace_root = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "ai-video-gui")
```

## 6. 自动化构建脚本

### 6.1 Windows 批处理脚本

在项目根目录创建 `build.bat`：

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo AI Video GUI - Windows 打包脚本
echo ========================================
echo.

:: 清理旧文件
echo [1/4] 清理旧打包文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist output rmdir /s /q output

:: PyInstaller 打包
echo.
echo [2/4] 运行 PyInstaller 打包...
uv run pyinstaller ai-video-gui.spec --clean
if errorlevel 1 (
    echo [错误] PyInstaller 打包失败！
    pause
    exit /b 1
)

:: 检查打包结果
echo.
echo [3/4] 检查打包结果...
if not exist "dist\ai-video-gui\ai-video-gui.exe" (
    echo [错误] 未找到可执行文件！
    pause
    exit /b 1
)

:: 生成安装程序
echo.
echo [4/4] 生成安装程序...
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    echo [警告] 未找到 Inno Setup，跳过安装程序生成
    echo [提示] 手动运行：%INNO_PATH% installer.iss
    goto :end
)

%INNO_PATH% installer.iss
if errorlevel 1 (
    echo [错误] 安装程序生成失败！
    pause
    exit /b 1
)

:end
echo.
echo ========================================
echo 打包完成！
echo ========================================
echo 可执行文件: dist\ai-video-gui\ai-video-gui.exe
echo 安装程序:   output\ai-video-gui-setup-*.exe
echo ========================================
pause
```

### 6.2 PowerShell 脚本（可选）

创建 `build.ps1`：

```powershell
# AI Video GUI - Windows 打包脚本（PowerShell 版本）

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Video GUI - Windows 打包脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 清理旧文件
Write-Host "[1/4] 清理旧打包文件..." -ForegroundColor Yellow
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "output" -Recurse -Force -ErrorAction SilentlyContinue

# PyInstaller 打包
Write-Host ""
Write-Host "[2/4] 运行 PyInstaller 打包..." -ForegroundColor Yellow
uv run pyinstaller ai-video-gui.spec --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] PyInstaller 打包失败！" -ForegroundColor Red
    exit 1
}

# 检查打包结果
Write-Host ""
Write-Host "[3/4] 检查打包结果..." -ForegroundColor Yellow
if (-not (Test-Path "dist\ai-video-gui\ai-video-gui.exe")) {
    Write-Host "[错误] 未找到可执行文件！" -ForegroundColor Red
    exit 1
}

# 生成安装程序
Write-Host ""
Write-Host "[4/4] 生成安装程序..." -ForegroundColor Yellow
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoPath)) {
    Write-Host "[警告] 未找到 Inno Setup，跳过安装程序生成" -ForegroundColor Yellow
    Write-Host "[提示] 手动运行：$innoPath installer.iss" -ForegroundColor Yellow
} else {
    & $innoPath installer.iss
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 安装程序生成失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "打包完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "可执行文件: dist\ai-video-gui\ai-video-gui.exe" -ForegroundColor White
Write-Host "安装程序:   output\ai-video-gui-setup-*.exe" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
```

## 7. 测试和发布

### 7.1 打包前测试清单

- [ ] 所有功能在开发环境正常运行
- [ ] 数据库迁移脚本已完成
- [ ] 日志配置正确（不依赖控制台输出）
- [ ] 所有资源文件（QML、图标、模板）已提交到 Git
- [ ] 版本号已更新（`pyproject.toml` 和 `installer.iss`）

### 7.2 打包后测试清单

- [ ] 在干净的 Windows 环境测试安装
- [ ] 测试所有核心功能（聊天、项目创建、视频生成）
- [ ] 检查数据库和配置文件是否正确创建在 `%LOCALAPPDATA%`
- [ ] 测试卸载程序是否清理干净
- [ ] 检查应用图标是否正确显示
- [ ] 测试开始菜单和桌面快捷方式

### 7.3 发布建议

1. **版本号规范**：遵循语义化版本（Semantic Versioning）
   - `0.1.0` - 初始版本
   - `0.2.0` - 新功能
   - `0.1.1` - Bug 修复

2. **发布渠道**：
   - GitHub Releases（推荐）
   - 官网下载页面
   - 微软应用商店（需注册开发者账号）

3. **文件命名**：
   ```
   ai-video-gui-setup-0.1.0-win64.exe
   ai-video-gui-0.1.0-portable-win64.zip  （免安装版）
   ```

4. **发布说明模板**：
   ```markdown
   ## AI Video GUI v0.1.0
   
   ### 新增功能
   - 聊天模式视频生成
   - 项目模式完整流程
   
   ### 系统要求
   - Windows 10/11（64 位）
   - 2GB RAM（推荐 4GB）
   - 500MB 磁盘空间
   
   ### 下载
   - [安装版](链接)
   - [免安装版](链接)
   
   ### 已知问题
   - 部分杀毒软件可能误报（已提交白名单申请）
   ```

## 8. 后续优化方向

### 8.1 代码签名（Code Signing）

- 购买代码签名证书（EV 证书优先）
- 使用 `signtool.exe` 签名 exe 文件
- 避免 Windows SmartScreen 警告

### 8.2 自动更新

- 集成 [WinSparkle](https://github.com/vslavik/winsparkle) 或 [PyUpdater](https://www.pyupdater.org/)
- 实现版本检查和增量更新

### 8.3 CI/CD 集成

- GitHub Actions 自动打包发布
- 多平台支持（macOS、Linux）

### 8.4 性能优化

- 使用 Nuitka 进一步优化启动速度
- 延迟加载非核心模块
- 资源文件压缩

## 9. 参考资料

- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)
- [Inno Setup 官方文档](https://jrsoftware.org/ishelp/)
- [PySide6 打包指南](https://doc.qt.io/qtforpython-6/deployment/index.html)
- [Windows 代码签名指南](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
