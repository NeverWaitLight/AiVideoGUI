# 打包指南

本文档说明如何在全新的 Windows 电脑上从零开始打包 AI Video GUI 安装程序。

## 前置要求

在开始打包前，请确保系统满足以下要求：

### 1. 操作系统
- Windows 10 或更高版本（64 位）

### 2. Git
- 用于克隆代码仓库
- 下载地址：https://git-scm.com/download/win
- 安装后在命令行中验证：`git --version`

### 3. Python 包管理器 uv
- 快速的 Python 包管理工具
- 安装命令（PowerShell）：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- 安装后重启终端，验证：`uv --version`

### 4. Inno Setup 6
- 用于生成 Windows 安装程序
- 下载地址：https://jrsoftware.org/isdl.php
- 下载文件：`innosetup-6.x.x.exe`（推荐 QuickStart Pack 版本）
- 默认安装路径：`C:\Program Files (x86)\Inno Setup 6\`
- 安装时选择所有组件

## 完整打包流程

### 步骤 1：克隆代码

打开命令提示符（cmd）或 PowerShell，执行：

```bash
git clone https://github.com/yourusername/ai-video-gui.git
cd ai-video-gui
```

### 步骤 2：安装依赖

在项目根目录执行：

```bash
uv sync
```

这会自动：
- 创建虚拟环境（`.venv/`）
- 安装所有 Python 依赖（包括 PyInstaller）
- 根据 `pyproject.toml` 和 `uv.lock` 锁定版本

**预计耗时**：2-5 分钟（取决于网络速度）

### 步骤 3：验证环境

运行开发版本测试环境是否正常：

```bash
dev.bat
```

如果应用能正常启动，说明环境配置成功。关闭应用继续下一步。

### 步骤 4：执行打包

在项目根目录执行：

```bash
build.bat
```

**打包过程说明**：
1. **清理旧文件**（1 秒）：删除 `build/`, `dist/`, `output/` 目录
2. **PyInstaller 打包**（1-2 分钟）：将 Python 代码和依赖打包成 exe
3. **Inno Setup 生成安装程序**（10-30 秒）：创建 Windows 安装包
4. **完成**：输出文件位置提示

**预计总耗时**：2-3 分钟

### 步骤 5：获取安装程序

打包完成后，安装程序位于：

```
output/AI-Video-GUI-Setup-1.0.0.exe
```

文件大小约 **100MB**，包含所有依赖，用户无需安装 Python。

## 输出文件说明

打包完成后会生成两种形式：

### 1. 免安装版（便携版）
- 位置：`dist/AI-Video-GUI/`
- 组成：
  - `AI-Video-GUI.exe` - 主程序
  - `_internal/` - 依赖文件夹
- 使用方式：直接运行 exe，或将整个文件夹复制到 U 盘/其他位置

### 2. 安装程序版
- 位置：`output/AI-Video-GUI-Setup-1.0.0.exe`
- 特性：
  - 带安装向导界面
  - 自动创建开始菜单快捷方式
  - 支持桌面快捷方式（可选）
  - 完整的卸载支持

## 测试安装程序

在分发前，建议先测试安装程序：

```bash
.\output\AI-Video-GUI-Setup-1.0.0.exe
```

**测试检查项**：
- [ ] 安装向导能正常显示
- [ ] 安装到指定目录成功
- [ ] 程序能正常启动
- [ ] 开始菜单快捷方式可用
- [ ] 卸载功能正常

## 配置文件说明

### `ai-video-gui.spec`
PyInstaller 配置文件，定义打包行为：

```python
# 关键配置项
datas=[
    ('qml', 'qml'),                      # QML 界面文件
    ('resources', 'resources'),          # 资源文件（图标、样式等）
    ('prompts/templates', 'prompts/templates'),  # AI 提示词模板
    ('alembic.ini', '.'),                # 数据库迁移配置
    ('alembic', 'alembic'),              # 数据库迁移脚本
]

hiddenimports=[
    'PySide6.QtCore',                    # Qt 核心模块
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickControls2',
    'sqlalchemy.ext.baked',              # SQLAlchemy 扩展
    'logging.config',                    # 日志配置
    'alembic.script',                    # Alembic 脚本
    'alembic.runtime.migration',         # Alembic 运行时
]

console=False  # 无控制台窗口（GUI 应用）
```

### `installer.iss`
Inno Setup 配置文件，定义安装程序行为：

```ini
; 应用信息
AppName=AI Video GUI
AppVersion=1.0.0
AppPublisher=WaitLight

; 安装路径
DefaultDirName={autopf}\AI Video GUI        ; C:\Program Files\AI Video GUI
DefaultGroupName=AI Video GUI               ; 开始菜单分组

; 权限
PrivilegesRequired=lowest                   ; 普通用户权限即可安装

; 文件源
Source: "dist\AI-Video-GUI\*"              ; 打包后的文件
DestDir: "{app}"                            ; 安装到应用目录

; 快捷方式
Name: "{group}\AI Video GUI"                ; 开始菜单
Name: "{autodesktop}\AI Video GUI"          ; 桌面（可选）
```

## 版本更新

修改版本号需要同步更新以下文件：

### 1. `installer.iss`（第 4 行）
```ini
#define MyAppVersion "1.0.1"  ; 修改版本号
```

### 2. `pyproject.toml`（可选，建议同步）
```toml
[project]
version = "1.0.1"
```

修改后重新运行 `build.bat` 即可。

## 常见问题排查

### 问题 1：`uv: command not found`
**原因**：uv 未安装或未添加到 PATH

**解决**：
1. 重新运行 uv 安装命令
2. 重启终端（让 PATH 生效）
3. 如果仍失败，手动添加 `%USERPROFILE%\.cargo\bin` 到系统 PATH

### 问题 2：`Inno Setup not found`
**原因**：Inno Setup 未安装或安装路径不同

**解决**：
1. 确认已安装 Inno Setup 6
2. 检查路径：`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
3. 如果安装在其他位置，修改 `build.bat` 第 13 行：
   ```batch
   set "INNO_SETUP=你的安装路径\ISCC.exe"
   ```

### 问题 3：PyInstaller 打包失败（`ModuleNotFoundError`）
**原因**：缺少隐藏导入

**解决**：
1. 查看错误信息中缺少的模块名（如 `No module named 'xxx'`）
2. 编辑 `ai-video-gui.spec`，在 `hiddenimports` 列表中添加：
   ```python
   hiddenimports=[
       # ... 现有的 ...
       'xxx',  # 添加缺少的模块
   ]
   ```
3. 重新运行 `build.bat`

### 问题 4：打包后程序无法启动（无错误提示）
**原因**：无窗口模式下错误信息被隐藏

**解决**：
1. 临时启用控制台查看错误：
   - 编辑 `ai-video-gui.spec`，修改 `console=True`
   - 重新打包：`uv run pyinstaller ai-video-gui.spec`
   - 运行 `dist\AI-Video-GUI\AI-Video-GUI.exe` 查看错误
2. 根据错误信息修复问题
3. 修复后改回 `console=False` 重新打包

### 问题 5：安装程序生成失败（语言文件缺失）
**错误信息**：`Couldn't open include file "ChineseSimplified.isl"`

**解决**：
已在 `installer.iss` 中使用英文界面，如需中文界面：
1. 确认 Inno Setup 安装了语言文件包
2. 或使用英文界面（当前配置）

### 问题 6：打包后文件过大
**正常大小**：
- 免安装版（`dist/`）：约 250-300 MB
- 安装程序：约 100 MB（压缩后）

**如果超过 500 MB**：
1. 检查是否包含了开发文件（`.venv/`, `.git/`）
2. 确认 `.spec` 文件的 `datas` 只包含必需文件

## 手动打包（高级）

如果需要分步调试，可以手动执行每个步骤：

### 1. 仅 PyInstaller 打包
```bash
uv run pyinstaller --clean -y ai-video-gui.spec
```

### 2. 测试 exe
```bash
cd dist\AI-Video-GUI
AI-Video-GUI.exe
```

### 3. 仅生成安装程序（假设已有 dist/）
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## 分发建议

### 文件校验
生成 SHA256 校验和（可选）：
```bash
certutil -hashfile output\AI-Video-GUI-Setup-1.0.0.exe SHA256
```

### 分发渠道
- GitHub Releases（推荐）
- 企业内网文件服务器
- 云盘分享（百度网盘、阿里云盘等）

### 用户安装要求
- **操作系统**：Windows 10 / 11（64 位）
- **磁盘空间**：至少 500 MB 可用空间
- **权限**：普通用户权限即可（无需管理员）
- **依赖**：无需预装 Python 或其他运行时

### 首次运行说明
告知用户：
1. 首次运行会自动创建数据目录：`%LOCALAPPDATA%\ai-video-gui\`
2. 需要配置 API Key 才能使用视频生成功能
3. 数据库会自动初始化，无需手动操作

## 开发环境说明

如果是开发者打包，注意以下事项：

### 开发与生产隔离
- **开发环境**：运行 `dev.bat`，数据存储在 `dev_workspace/`
- **生产环境**：运行 `uv run main.py`，数据存储在 `%LOCALAPPDATA%\ai-video-gui\`
- **安装版本**：数据存储在 `%LOCALAPPDATA%\ai-video-gui\`

三者完全隔离，可以同时运行。

### 清理构建产物
```bash
# 清理所有构建文件
rm -rf build dist output

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
```

## 快捷命令汇总

```bash
# 克隆代码
git clone https://github.com/yourusername/ai-video-gui.git
cd ai-video-gui

# 安装依赖
uv sync

# 开发环境运行
dev.bat

# 完整打包（生成安装程序）
build.bat

# 快速打包（仅免安装版）
build-simple.bat
```

## 技术支持

如果遇到本文档未覆盖的问题，请：
1. 查看项目 README.md 了解项目架构
2. 查看 CLAUDE.md 了解详细技术实现
3. 提交 Issue 到 GitHub 仓库
4. 联系项目维护者

---

**最后更新**：2026-08-10
**适用版本**：v1.0.0 及以上
