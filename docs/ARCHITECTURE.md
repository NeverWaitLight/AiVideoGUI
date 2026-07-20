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
