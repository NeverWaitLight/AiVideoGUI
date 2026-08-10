# 自动更新功能说明

## 功能概述

应用支持自动检查 GitHub Release 更新，并提供自动下载和安装功能。

## 实现组件

### 1. UpdateService (`service/update_service.py`)
- **检查更新**：调用 GitHub API 获取最新 release 信息
- **版本比较**：使用 `packaging` 库比较版本号
- **自动下载**：流式下载安装包到工作目录的 `updates/` 子目录
- **进度回调**：支持下载进度实时反馈
- **启动安装**：下载完成后自动启动安装程序

### 2. UpdateBridge (`bridge/update_bridge.py`)
- **DownloadWorker**：后台线程处理下载任务，避免阻塞 UI
- **信号机制**：
  - `update_available` - 发现新版本
  - `download_progress` - 下载进度更新
  - `download_finished` - 下载完成
  - `download_failed` - 下载失败
- **方法**：
  - `check_update()` - 检查更新
  - `download_update(url)` - 开始下载
  - `install_update(path)` - 启动安装程序

### 3. UpdateDialog (`qml/dialogs/UpdateDialog.qml`)
- **版本信息展示**：对比当前版本和最新版本
- **更新说明**：显示 Release Notes
- **下载进度条**：实时显示下载进度和速度
- **三种下载模式**：
  - **立即下载**：对话框保持打开，显示下载进度
  - **后台下载**：关闭对话框，后台静默下载
  - **稍后提醒**：关闭对话框，不下载
- **安装确认**：下载完成后弹出确认对话框
- **自动退出**：确认安装后自动关闭应用，启动安装程序

### 4. 设置页面"关于"标签页
- 显示当前应用版本（从 `Qt.application.version` 读取）
- 提供"检查更新"按钮
- 显示 GitHub 项目链接（可点击）

## 使用流程

### 自动检查（应用启动时）
1. 应用启动后自动调用 `bridge.update.check_update()`
2. 如果有新版本，自动弹出 `UpdateDialog`
3. 用户选择下载方式：
   - **立即下载** → 显示进度条 → 下载完成 → 弹出安装确认
   - **后台下载** → 关闭对话框 → 后台下载 → 完成后弹出安装确认
   - **稍后提醒** → 关闭对话框，不下载

### 手动检查（设置页面）
1. 打开设置对话框 → "关于"标签页
2. 点击"检查更新"按钮
3. 如果有新版本，弹出 `UpdateDialog`
4. 流程同上

### 安装流程
1. 下载完成后，弹出安装确认对话框
2. 用户选择：
   - **立即安装** → 启动安装程序 → 应用自动退出（`Qt.quit()`）
   - **稍后安装** → 关闭对话框，安装包保存在 `<workspace>/updates/` 目录

## 文件位置

- **下载目录**：`%LOCALAPPDATA%\ai-video-gui\updates\`
- **文件命名**：从 URL 提取文件名（如 `AI-Video-GUI-Setup-0.2.0.exe`）

## 版本号管理

- **存储位置**：`pyproject.toml` 的 `project.version` 字段
- **读取时机**：应用启动时通过 `tomllib` 读取
- **注入方式**：存入 DI 容器的 `config.app_version`
- **QML 访问**：通过 `Qt.application.version` 属性

## GitHub Release 要求

- **Tag 格式**：必须以 `v` 开头（如 `v0.2.0`）
- **安装包**：建议上传 Windows 安装包（文件名包含 `.exe`、`windows` 或 `win`）
- **Release Notes**：Release body 中的内容会显示在更新对话框中

## 依赖

- `packaging` - 版本号比较（支持语义化版本）
- `requests` - GitHub API 调用和文件下载

## 安全考虑

- 使用 HTTPS 协议下载（GitHub 官方地址）
- 下载完成后不自动安装，需要用户确认
- 安装程序由 Windows 系统验证数字签名（如果有）

## 测试

运行单元测试：
```bash
uv run python -m unittest tests.test_update_service -v
```

测试覆盖：
- 检查更新逻辑（有新版本、无新版本、网络错误）
- 版本号比较
- GitHub API 响应解析
