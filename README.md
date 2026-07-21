Windows 桌面端 AI 视频生成工具。用户通过聊天界面输入文字描述，程序调用大模型 API 生成视频并自动下载到本地。支持接入多家大模型厂商，通过统一的 Provider 抽象层切换。

## 技术选型

- **语言：** Python 3.14
- **包管理：** uv
- **GUI 框架：** PyQt6 + PyQt6-Fluent-Widgets — 现代化的 Fluent Design 界面组件库
- **HTTP：** requests（同步调用）+ 异步下载用 requests 流式写入
- **本地存储：** SQLite（对话历史）+ 本地文件系统（视频文件）
- **配置：** JSON 配置文件，存放 API Key、默认模型等用户设置

## 整体架构

程序分为三层，职责清晰，层间通过明确接口通信：

**界面层（UI）** 负责所有用户交互，不包含业务逻辑。包含聊天主窗口、消息气泡、侧边栏、设置面板等组件。

**业务层（Service）** 协调界面和底层 Provider，管理对话会话的生命周期，处理异步任务轮询和视频下载流程。

**供应商层（Provider）** 封装各家大模型 API 的调用细节，对外暴露统一接口，新增厂商只需实现该接口。

## 界面设计

采用现代化的 **Fluent Design** 设计语言，提供流畅一致的用户体验。

整体布局为经典的左右分栏：

**左侧边栏**
- 顶部：新建对话按钮（PrimaryPushButton）
- 中部：历史对话列表（ListWidget），每条显示对话标题（取首条消息摘要）和时间，支持右键菜单删除
- 底部：素材库和设置入口（API Key 管理、默认模型选择、下载目录配置）

**右侧主区域**
- 顶部：当前对话标题 + 当前选中的模型名称
- 中部：消息流区域，用户消息靠右，AI 回复靠左；AI 回复中嵌入视频预览（缩略图 + 播放按钮），下方显示下载状态（生成中 → 下载中 → 已完成 + 本地路径）
- 底部：参数面板（分辨率、时长、比例、自动优化、水印等选项）+ 输入框（TextEdit）+ 发送按钮（PrimaryPushButton），支持 Enter 发送、Shift+Enter 换行

**Fluent 组件特性**
- **现代化按钮**：PrimaryPushButton（主要操作）、PushButton（次要操作），自带悬停和点击动效
- **流畅输入框**：LineEdit 和 TextEdit 带有聚焦高亮效果
- **图标系统**：使用 FluentIcon 枚举提供一致的图标风格
- **对话框**：Dialog 和 MessageBox 采用圆角、阴影设计
- **菜单**：RoundMenu 提供圆角卡片式上下文菜单
- **开关和进度**：SwitchButton、ProgressBar、IndeterminateProgressBar 等现代化控件

**视频状态流转**
- 发送 prompt 后显示"生成中…"（IndeterminateProgressBar）
- Provider 返回任务 ID 后进入轮询，显示进度（如 API 支持）
- 视频就绪后自动开始下载，显示下载进度条（ProgressBar）
- 下载完成后显示本地视频播放器 + "打开文件夹"按钮

## Provider 抽象设计

这是整个架构的核心扩展点。定义一个 VideoProvider 基类（抽象类），所有厂商实现类必须继承并实现以下方法：

**submit(prompt, params) -> task_id**
提交生成任务。prompt 为用户输入的文字描述，params 为可选参数（分辨率、比例、时长等），返回一个任务 ID 用于后续查询。

**check_status(task_id) -> TaskStatus**
查询任务状态。返回一个统一的状态枚举：PENDING（排队中）、RUNNING（生成中）、SUCCEEDED（已完成，附带视频 URL）、FAILED（失败，附带错误信息）。

**download(video_url, save_path) -> local_path**
下载视频到指定本地路径。支持进度回调，返回最终文件路径。

**get_model_info() -> ModelInfo**
返回当前 Provider 支持的模型列表及其参数能力（支持的分辨率、最大时长等），供界面层动态渲染选项。

**已规划的 Provider 实现：**
- DashScopeProvider — 阿里万象（wan2.7-t2v），异步模式，通过 X-DashScope-Async 头启用，需轮询任务状态
- 后续可扩展：字节火山引擎、智谱清影、快手可灵等

## 存储设计

采用双存储策略，按数据性质分开管理：

**SQLite — 对话与任务状态**
存储 Conversation 和 Message 两张表。对话历史是关系型数据（一对多），任务状态需要频繁原子更新（生成中 → 下载中 → 完成），SQLite 的事务和查询能力正好满足。数据库文件存放在应用数据目录下，单文件便于备份。

主要表结构：
- conversations 表：id、title、created_at、model_name、provider_name
- messages 表：id、conversation_id（外键）、role、content、task_id、video_url、local_path、status、created_at

**JSON 文件 — 应用配置**
存储 Provider 凭证和用户偏好设置。配置项少、结构简单、用户偶尔需要手动编辑，JSON 比 SQLite 更合适。配置文件存放在用户目录下，不进入版本控制。

配置内容：
- providers 列表：每项包含 provider_name、api_key、base_url、default_model、default_params
- app_settings：默认下载目录、默认 Provider、主题等全局设置

## 运行时文件与日志

程序在用户系统上使用以下目录结构，遵循 Windows 应用数据惯例：

**应用数据根目录**
`%LOCALAPPDATA%\ai-video-gui\`，所有持久化文件集中存放在此：
- ai-video-gui.db — SQLite 数据库文件
- config.json — 应用配置（Provider 凭证 + 全局设置）
- logs/ — 日志文件目录（详见下方日志规范）

**临时文件目录**
`%TEMP%\ai-video-gui\`，存放下载过程中的临时文件（如未完成的视频下载）。程序正常退出时自动清理；异常退出时下次启动时清理。

**视频下载目录**
- 默认路径：`%USERPROFILE%\Videos\AI-Video-GUI\`，跟随系统视频目录惯例，用户无需额外配置即可找到
- 用户可在设置面板中自定义下载路径，自定义路径保存在 config.json 的 app_settings.default_download_dir 中
- 视频文件命名规则：`{日期}_{时间}_{模型名}_{prompt前20字}.mp4`，避免文件名冲突且便于识别

**日志规范**

使用 Python 标准库 logging 模块，不引入第三方日志框架。

日志级别策略：
- DEBUG — 开发调试信息：函数入参、API 请求/响应原文、SQL 语句。仅开发环境开启
- INFO — 正常运行关键事件：程序启动/退出、对话创建、视频提交/完成/下载完成、Provider 切换
- WARNING — 可恢复的异常：API 超时重试、下载中断重连、配置缺失使用默认值
- ERROR — 不可恢复的错误：API 调用失败、下载最终失败、数据库写入异常。记录完整异常栈

日志格式：`时间 | 级别 | 模块名 | 消息`

日志文件策略：
- 使用 RotatingFileHandler 按大小滚动，单文件上限 5MB，保留最近 5 个文件
- 日志文件名：`ai-video-gui.log`（当前）、`ai-video-gui.log.1` ~ `ai-video-gui.log.5`（历史）
- 程序启动时记录一条 INFO 日志，包含版本号、Python 版本、操作系统信息，便于排查问题

各模块日志归属：
- providers/ — 记录 API 请求地址、响应状态码、轮询次数（DEBUG 级别记录完整请求体和响应体）
- service/ — 记录任务生命周期事件（提交、状态变更、下载开始/完成）
- storage/ — 记录数据库操作（建表、迁移、异常）
- ui/ — 仅在 ERROR 级别记录界面异常

## 数据模型

以下为程序内部的数据类定义，与存储层对应：

**Conversation（对话）→ SQLite conversations 表**
- id、title（自动生成）、created_at、model_name、provider_name

**Message（消息）→ SQLite messages 表**
- id、conversation_id、role（user/assistant）、content、task_id、video_url、local_path、status、created_at

**ProviderConfig（供应商配置）→ JSON 配置文件**
- provider_name、api_key、base_url、default_model、default_params

**AppSettings（全局设置）→ JSON 配置文件**
- default_provider、default_download_dir、theme

## 项目结构

- main.py — 程序入口，初始化应用和主窗口
- ai-video-gui.spec — PyInstaller 打包配置
- .github/workflows/ — GitHub Actions 流水线定义
- ui/ — 界面层：主窗口、侧边栏、聊天组件、设置面板
- service/ — 业务层：对话管理、任务调度、下载管理
- providers/ — 供应商层：基类定义 + 各厂商实现
- models/ — 数据模型：Conversation、Message、ProviderConfig
- storage/ — SQLite 数据库操作：建表、对话和消息的增删改查（数据库文件在 %LOCALAPPDATA%\ai-video-gui\）
- config/ — JSON 配置文件读写：Provider 凭证和全局设置（配置文件在 %LOCALAPPDATA%\ai-video-gui\）

## 构建与运行

**开发环境依赖：**
- Python 3.14+
- uv 包管理器
- PyQt6 6.11.0+
- PyQt6-Fluent-Widgets 1.11.2+

**启动步骤：**
- 安装依赖：`uv sync`
- 启动程序：`uv run main.py`
- 首次启动时会弹出设置面板，引导用户配置至少一个 Provider 的 API Key

**主题配置：**
- 默认使用浅色 Fluent Design 主题
- 主题色为 `#4A90D9`（蓝色），可在 `ui/styles.py` 的 `apply_fluent_theme()` 函数中修改
- 支持切换深色模式（修改 `setTheme(Theme.DARK)`）

## 打包与发布

使用 PyInstaller 将程序打包为 Windows 可执行文件，通过 GitHub Actions 自动化构建和发布。

**打包工具：PyInstaller**
- 将 Python 解释器、PyQt6、所有依赖打包为单个 .exe 文件（--onefile 模式）
- 用户无需安装 Python 环境，双击即可运行
- 打包配置文件 .spec 放在项目根目录，定义入口、图标、数据文件等

**版本管理**
- 版本号统一维护在 pyproject.toml 的 version 字段
- PyInstaller 打包时读取该版本号，用于可执行文件命名和 Windows 文件属性

**GitHub Actions 流水线**

触发条件：
- 推送 `v*` 格式的 tag（如 v0.1.0）时触发完整打包 + 发布
- 推送到 main 分支时触发打包验证（构建但不发布，确保打包流程不会 break）

运行环境：
- 使用 windows-latest runner，确保在 Windows 环境下构建

流水线步骤：
- 检出代码 → 安装 Python 3.14 → 安装 uv → `uv sync` 安装依赖
- 运行 `pyinstaller ai-video-gui.spec` 生成可执行文件
- 将产物上传为 GitHub Actions Artifact
- 如果是 tag 触发，自动创建 GitHub Release，将 .exe 作为 Release Asset 发布

产物命名：
- `ai-video-gui-{版本号}-windows-x64.exe`

**本地打包验证**
- 开发时可在本地执行 `uv run pyinstaller ai-video-gui.spec` 验证打包是否正常
- 打包产物输出到 dist/ 目录（已在 .gitignore 中排除）

## 开发约定

- 使用 uv 管理依赖，不手动操作 pip
- UI 组件统一使用 PyQt6-Fluent-Widgets，不直接使用原生 PyQt6 控件（除非 Fluent 库未提供）
- 主题配置统一在 `ui/styles.py` 中管理，不使用内联 QSS 样式
- 新增 UI 组件时优先查阅 [QFluentWidgets 文档](https://qfluentwidgets.com/)
- Provider 新增时只需在 providers/ 下添加实现类，并在配置中注册，不改动业务层和界面层代码
- API Key 等敏感信息存储在本地配置文件中，不进入版本控制
- 界面层不直接调用 Provider，一律通过 Service 层中转

**Fluent 组件使用规范：**
- 主要操作按钮使用 `PrimaryPushButton`
- 次要操作按钮使用 `PushButton`
- 输入框使用 `LineEdit` 或 `TextEdit`
- 下拉框使用 `ComboBox`
- 对话框使用 `Dialog` 或 `MessageBox`
- 菜单使用 `RoundMenu` + `Action`
- 图标使用 `FluentIcon` 枚举
- 进度条使用 `ProgressBar` 或 `IndeterminateProgressBar`
- 开关使用 `SwitchButton`

详见 `FLUENT_MIGRATION.md` 获取完整的组件迁移指南。

## 版本记录

| Tag | 日期 | 说明 |
|-----|------|------|
| `v_demo` | 2026-07-21 | 项目管理链路粗放板，生成视频链路完成 |
