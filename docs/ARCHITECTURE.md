## 全局任务轮询服务

任务轮询与前端 UI 完全解耦，由独立的 `TaskPollingService` 管理。应用启动时自动运行，根据 `active_tasks` 表状态自动启停。

**核心类：**

- **`TaskPollingService`** — 服务管理类，负责启动/停止轮询线程，提供信号接口（`status_changed`、`download_progress`、`task_finished`、`task_failed`），管理 Provider 实例池
- **`_PollingWorker`** — 后台 QThread，周期性扫描 `active_tasks` 表，根据任务创建时间判断是否开始轮询（初始延迟 5 分钟）

**轮询策略：**

- **活跃模式：** 有任务时每 30 秒轮询一次
- **空闲模式：** 表空时每 60 秒低频检查
- **初始延迟：** 新任务提交后等待 5 分钟再开始轮询（避免无效请求）
- **最大次数：** 单任务最多轮询 50 次后标记失败

**架构优势：** 用户切换对话、关闭页面不影响后台任务；全局单线程取代每任务一线程；应用崩溃重启后自动恢复所有未完成任务；信号接口与原 VideoService 一致，前端无需修改。

## 视频元数据提取

通过 ffmpeg-python 为视频文件自动提取元数据，在视频下载完成和手动导入两个场景触发，无需手动调用。

**提取内容：** 视频时长（秒）、分辨率（宽×高）、文件大小、缩略图（320px 宽 JPEG，截取第 1 秒画面）。

**工具类：** `VideoMetadataExtractor`（位于 `utils/video_metadata.py`），提供三个静态方法：

- **`extract_metadata()`** — 仅提取时长、分辨率、文件大小
- **`generate_thumbnail()`** — 仅生成缩略图
- **`extract_all()`** — 一站式提取元数据并生成缩略图

**缩略图管理：** 统一存储在 `下载目录/.thumbnails/` 子目录，命名规则为 `{视频文件名}_thumb.jpg`。删除素材时同步清理对应缩略图。

**容错设计：** ffmpeg 缺失或提取失败时记录 WARNING 日志，元数据字段使用默认值（0），不影响视频下载和导入主流程。

**数据库变更：** `media_files` 表新增 `thumbnail_path`（TEXT）、`duration`（REAL）、`width`（INTEGER）、`height`（INTEGER）四列，应用启动时通过 `_migrate()` 自动增量迁移，已有记录填充默认值。

**数据流：** 视频文件 → `VideoMetadataExtractor.extract_all()` → `MediaFile` 对象（携带元数据） → `DatabaseManager.add_media_file()` → SQLite `media_files` 表。

## SQLite 数据库类型约定

SQLAlchemy 映射到 SQLite 时需遵循以下类型规则：

**SQLite 存储类型：**

| SQLite 存储类 | 含义            | 示例        |
| ---------- | ------------- | --------- |
| `NULL`     | 空值            | `NULL`    |
| `INTEGER`  | 有符号整数，最多 64 位 | `123`     |
| `REAL`     | 64 位 IEEE 浮点数 | `3.14`    |
| `TEXT`     | 文本字符串         | `'hello'` |
| `BLOB`     | 二进制数据         | 图片、文件等    |

**SQLAlchemy 类型映射规则：**

本项目使用 SQLite 作为数据库。SQLite 的 `INTEGER` 是 64 位有符号整数（-2^63 到 2^63-1），足以容纳任何整数需求（包括 13 位毫秒时间戳）。

1. **自增主键** → `mapped_column(Integer, primary_key=True, autoincrement=True)`
   - SQLite 只对 `INTEGER PRIMARY KEY` 支持自动递增
   - 必须使用 `Mapped[Optional[int]]` 类型标注（允许创建时为 None）
   - 示例：`id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True)`

2. **所有其他整数字段** → `mapped_column(Integer)`
   - 外键引用、毫秒时间戳、文件大小、计数等统一使用 `Integer`
   - 示例：
     ```python
     project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ...))
     created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位毫秒时间戳
     file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
     ```

**关键理解：**
- SQLite 的 `INTEGER` 是 64 位，足以存储任何整数需求
- 所有整数字段统一使用 `Integer` 类型，无需区分大小
- 自增主键必须使用 `Optional[int]` 类型标注

## ORM 事件监听器自动保存历史

使用 SQLAlchemy 的事件监听机制实现历史版本自动保存，业务代码无需关心历史持久化逻辑。

**核心组件：** `history_listener.py`（位于 `storage/orm/`），在应用启动时由 `init_engine()` 自动注册监听器。

**监听策略：**

- **StoryOutlineEntity** — 监听 `after_update` 事件，仅在 `content` 字段变化时保存历史到 `story_outline_history` 表（避免 `updated_at` 更新触发重复保存）
- **CharacterEntity** — 监听 `after_update` 事件，仅在关键字段（`name`、`ref_code`、`description`、`design_image`）变化时保存历史到 `character_history` 表
- **防重复注册** — 使用全局标志 `_listeners_registered` 确保监听器仅注册一次（测试环境多次初始化引擎时的保护机制）

**历史表设计约定：**

- **`story_outline_id`** — 指向原始故事大纲实体的外键
- **`project_id`** — 冗余字段，方便按项目查询历史记录
- **`created_at`** — 历史版本创建时间
- **内容字段** — `content`（StoryOutline）或 `snapshot`（Character，JSON 序列化）

**架构优势：** 历史保存与业务逻辑解耦；所有 Entity 更新自动触发，不会遗漏；扩展新实体只需在监听器中注册；修改历史逻辑只需改一处代码。

**已实现的监听器：** StoryOutline（故事大纲）、Character（角色）。Script 和 Shot 因需要序列化关联实体（场次/分镜列表），仍保留手动保存逻辑。

