# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Windows 桌面端 AI 视频生成工具。用户通过 PyQt6 聊天界面输入文字描述，程序调用大模型 API（当前支持阿里万象 DashScope）生成视频，并通过后台线程轮询任务状态和自动下载到本地。

**技术栈：** Python 3.14 + PyQt6 + requests + SQLite

## Development Commands

```bash
# 安装依赖（使用 uv 包管理器）
uv sync

# 启动应用
uv run main.py

# 运行测试（项目中有测试文件，但未配置测试运行器）
uv run python -m pytest tests/
# 或
uv run python -m unittest discover tests/
```

## Architecture

采用三层架构，职责清晰分离：

### 1. UI Layer (`ui/`)
- **main_window.py** - 主窗口容器，初始化基础设施（Database/Config/Service），协调所有组件
- **sidebar.py** - 左侧边栏（240px 固定宽度），包含新建对话按钮、历史对话列表、设置按钮
- **chat_area.py** - 右侧聊天区域，包含标题栏、消息滚动区、输入框
- **widgets.py** - 自定义组件：`MessageBubble`（聊天气泡）、`VideoStatusCard`（视频状态卡片）
- **settings_dialog.py** - 设置对话框（Provider 配置 + 应用设置）
- **styles.py** - 全局 QSS 样式表和颜色常量

**信号驱动：** 组件通过 PyQt6 信号槽机制通信，避免直接耦合

### 2. Service Layer (`service/`)
- **video_service.py** - 轻量级服务，仅负责对话/消息 CRUD 和任务提交
  - `VideoService` - 管理 Provider 实例、对话管理、任务提交到数据库
  - `_PROVIDER_REGISTRY` - Provider 注册表，扩展新供应商时在此注册

- **task_polling_service.py** - 全局任务轮询服务（独立后台线程）
  - `TaskPollingService` - 应用启动时运行，数据库驱动的轮询服务
  - `_PollingWorker` (QThread) - 周期性扫描 `active_tasks` 表，按任务创建时间执行轮询策略
  - 表空时自动暂停（低频检查），有新任务时恢复活跃轮询
  - 完全解耦前端页面状态，通过信号通知 UI 更新

**任务流程（解耦版）：** 
1. UI 提交任务 → VideoService 写入 `active_tasks` 表
2. TaskPollingService 检测到新任务 → 等待初始延迟（默认 5 分钟）
3. 周期轮询状态（30 秒间隔，最多 50 次）→ 下载视频 → 发出完成信号
4. 任务完成后从 `active_tasks` 表移除

### 3. Provider Layer (`providers/`)
- **base.py** - `VideoProvider` 抽象基类，定义统一接口：
  - `submit(prompt, params)` - 提交生成任务，返回 task_id
  - `check_status(task_id)` - 查询任务状态，返回 TaskResult
  - `download(video_url, save_path, progress_callback)` - 流式下载视频
  - `get_model_info()` - 返回模型能力信息
  
- **dashscope.py** - 阿里万象 DashScope 实现
  - 使用异步模式（`X-DashScope-Async: enable`）
  - API Base URL: `https://dashscope.aliyuncs.com/api/v1`
  - 默认模型：`wan2.7-t2v`

**扩展新 Provider：** 实现 `VideoProvider` 的 4 个抽象方法，在 `_PROVIDER_REGISTRY` 注册，在 UI 的 `_PROVIDER_OPTIONS` 和 `_MODEL_OPTIONS` 添加选项

### 4. Data Layer

**storage/database.py** - SQLite 数据库管理
- `conversations` 表 - 对话元数据（id, title, created_at, model_name, provider_name）
- `messages` 表 - 消息记录（id, conversation_id, role, content, task_id, video_url, local_path, status）
- `active_tasks` 表 - 活跃任务追踪
- `_migrate()` 方法 - 增量 schema 迁移

**config/manager.py** - JSON 配置管理
- 配置路径：`%LOCALAPPDATA%\ai-video-gui\config.json`
- 管理 Provider 凭证（api_key, base_url, default_model）和应用设置（下载目录、默认 Provider）

**models/data_models.py** - 数据类定义
- 使用 `@dataclass` 定义所有数据结构
- 包含 `TaskStatus`, `MessageStatus` 枚举

## Key Design Patterns

1. **全局轮询服务** - TaskPollingService 独立于 UI 页面状态，应用启动时运行，通过 `active_tasks` 表驱动
2. **信号槽机制** - UI 和 Service 通过 PyQt6 信号实现线程安全的异步通信
3. **注册表模式** - Provider 通过 `_PROVIDER_REGISTRY` 字典注册，支持动态加载
4. **工厂模式** - VideoService 根据 provider_name 延迟实例化并缓存 Provider 对象
5. **后台线程** - 使用 `QThread` + 可中断 sleep 机制避免僵尸线程
6. **数据库驱动轮询** - 轮询服务根据 `active_tasks` 表自动启停，表空时暂停（60 秒低频检查），有任务时活跃轮询（30 秒间隔）

## File Locations

**应用数据目录：** `%LOCALAPPDATA%\ai-video-gui\`
- `ai-video-gui.db` - SQLite 数据库
- `config.json` - 应用配置和 API Key
- `logs/` - 日志文件（RotatingFileHandler，5MB × 5 文件）

**临时文件：** `%TEMP%\ai-video-gui\` - 下载中的 .part 文件

**默认下载目录：** `%USERPROFILE%\Videos\AI-Video-GUI\`（用户可在设置中自定义）

## Important Conventions

### 日志记录
- 使用 Python 标准库 `logging`
- 每个模块：`logger = logging.getLogger(__name__)`
- 级别使用：DEBUG（API 请求/响应）、INFO（业务事件）、WARNING（可恢复异常）、ERROR（不可恢复错误）

### 错误处理
- **Provider 层：** HTTP 错误抛出给上层，业务错误抛出 `RuntimeError`
- **Service 层：** Worker 线程捕获所有异常，通过 `failed` 信号传递错误消息
- **UI 层：** 仅在异常处理器中记录日志，不在正常流程打日志

### 依赖管理
- **仅使用 uv** 管理依赖，不手动操作 pip
- 当前依赖：`pyqt6>=6.11.0`, `requests>=2.34.2`, `rich>=15.0.0`
- 添加新依赖：`uv add <package>`

### API Key 管理
- **绝不硬编码** API Key 或敏感信息
- 存储在 JSON 配置文件（`config.json`），通过 `.gitignore` 排除版本控制
- UI 使用密码模式输入框（`setEchoMode(QLineEdit.EchoMode.Password)`）

### 线程安全
- UI 更新必须在主线程执行
- Worker 线程通过信号与 UI 通信，不直接调用 UI 方法
- `VideoService.shutdown()` 负责优雅停止所有后台线程

## Testing

测试文件位于 `tests/` 目录：
- `test_service_flow.py` - Service 层集成测试
- `test_settings.py` - 配置管理测试
- `test_ui_integration.py` - UI 集成测试

**注意：** 项目尚未配置自动化测试运行器，需手动执行

## Common Tasks

### 添加新的视频生成供应商

1. 在 `providers/` 创建新文件（如 `volcano.py`）
2. 继承 `VideoProvider` 并实现 4 个抽象方法
3. 在 `service/video_service.py` 的 `_PROVIDER_REGISTRY` 注册
4. 在 `ui/settings_dialog.py` 的 `_PROVIDER_OPTIONS` 和 `_MODEL_OPTIONS` 添加 UI 选项
5. 更新配置文件 schema（如需要新字段）

### 修改任务轮询策略

在 `service/task_polling_service.py` 的 `TaskPollingService.__init__()` 中调整：
- `poll_interval` - 任务状态检查间隔（默认 30 秒）
- `initial_delay` - 新任务提交后的初始等待时间（默认 300 秒）
- `idle_check_interval` - 空闲时检查表是否有新任务的间隔（默认 60 秒）
- `max_polls_per_task` - 单个任务最大轮询次数（默认 50 次）

**注意：** 轮询服务在应用启动时自动运行，不需要手动触发。任务完成后会自动从 `active_tasks` 表移除。

### 修改 UI 样式

在 `ui/styles.py` 中修改：
- 颜色常量（`COLOR_*` 变量）
- QSS 样式表字符串（`*_STYLE` 变量）

### 数据库 Schema 迁移

在 `storage/database.py` 的 `_migrate()` 方法中添加迁移逻辑：
```python
# 检查列是否存在
cursor.execute("PRAGMA table_info(messages)")
columns = {col[1] for col in cursor.fetchall()}
if "new_column" not in columns:
    cursor.execute("ALTER TABLE messages ADD COLUMN new_column TEXT")
```

## Windows-Specific Notes

- 使用 `os.path.expandvars()` 展开 Windows 环境变量（如 `%LOCALAPPDATA%`）
- 使用 `os.startfile(path)` 打开视频文件（调用系统默认播放器）
- 使用 `subprocess.run(["explorer", "/select,", path])` 在资源管理器中定位文件
- 路径处理使用 `pathlib.Path` 确保跨平台兼容性（虽然当前仅支持 Windows）

## Known Limitations

- **单一 Provider 实现：** 当前仅支持 DashScope，其他供应商需扩展
- **无打包配置：** README 中提到 PyInstaller 和 GitHub Actions，但项目中缺少 `ai-video-gui.spec` 和 `.github/workflows/` 文件
- **无自动化测试：** 测试文件存在但未集成到 CI/CD
- **仅支持 Windows：** 代码中有大量 Windows 特定逻辑（`os.startfile`, `explorer`, `%LOCALAPPDATA%`）
