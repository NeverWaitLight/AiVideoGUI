# 架构重构：全局任务轮询服务

## 重构目标

将视频任务轮询逻辑从前端页面状态解耦，实现一个独立的后台轮询服务，应用启动时自动运行，根据 `active_tasks` 表的状态自动启停。

## 主要变更

### 1. 新增 `service/task_polling_service.py`

创建了全局任务轮询服务，包含两个核心类：

- **`TaskPollingService`** - 服务管理类，负责启动/停止轮询线程
  - 提供与原 `VideoService` 相同的信号接口（`status_changed`, `download_progress`, `task_finished`, `task_failed`）
  - 管理 Provider 实例池
  - 配置轮询策略参数

- **`_PollingWorker`** - 后台 QThread 线程
  - 周期性扫描 `active_tasks` 表
  - 根据任务创建时间判断是否需要轮询（初始延迟 5 分钟）
  - 表空时进入空闲模式（60 秒低频检查）
  - 有任务时活跃轮询（30 秒间隔）
  - 任务完成后自动从表中移除

### 2. 简化 `service/video_service.py`

- 移除 `_TaskWorker` 类（不再需要每任务一个线程）
- 移除 `resume_pending_tasks()` 方法（由 `TaskPollingService` 自动处理）
- 移除 `shutdown()` 方法（不再管理 worker 线程）
- 移除所有信号定义（由 `TaskPollingService` 提供）
- 简化为纯粹的对话管理和任务提交服务

### 3. 更新 `ui/main_window.py`

- 初始化时创建独立的 `TaskPollingService` 实例
- 将信号连接从 `VideoService` 改为 `TaskPollingService`
- 启动时调用 `polling_service.start()`（自动恢复未完成任务）
- 关闭时调用 `polling_service.shutdown()`

### 4. 数据库 Schema 更新

- `storage/database.py` 的 `list_active_tasks()` 现在返回 `created_at` 字段（datetime 对象）
- 用于计算任务是否已过初始延迟期

## 架构优势

### 解耦设计
- 任务轮询与 UI 页面状态完全独立
- 用户切换对话、关闭页面不影响后台任务
- 应用重启后自动恢复所有未完成任务

### 资源效率
- 全局单线程轮询，取代原来的每任务一线程模式
- 表空时自动暂停，节省 CPU 资源
- 有任务时立即恢复，无需手动触发

### 数据库驱动
- 轮询状态完全由 `active_tasks` 表决定
- 任务状态持久化，应用崩溃后可恢复
- 多实例部署时支持任务分布（未来扩展）

## 配置参数

在 `TaskPollingService.__init__()` 中可调整：

```python
self.poll_interval = 30.0           # 任务状态检查间隔（秒）
self.initial_delay = 300.0          # 新任务初始等待时间（秒）
self.idle_check_interval = 60.0     # 空闲时检查间隔（秒）
self.max_polls_per_task = 50        # 单任务最大轮询次数
```

## 测试覆盖

新增 `tests/test_polling_service.py`：

- ✅ 轮询服务启动/停止
- ✅ 空闲模式（表空时）
- ✅ 完整任务轮询工作流（提交 → 轮询 → 下载 → 完成）

## 兼容性

- 前端 UI 无需任何修改（信号接口保持一致）
- 现有 Provider 实现无需修改
- 数据库 Schema 向后兼容（已有 `created_at` 字段）

## 迁移路径

对于已有代码：

1. 将 `VideoService` 的信号连接改为 `TaskPollingService`
2. 移除 `VideoService.resume_pending_tasks()` 调用
3. 在应用启动时调用 `TaskPollingService.start()`
4. 在应用关闭时调用 `TaskPollingService.shutdown()`

## 未来扩展

- 支持优先级队列（高优先级任务更短延迟）
- 支持多实例分布式轮询（通过数据库锁）
- 支持轮询策略热更新（通过配置文件）
- 支持任务失败重试策略（指数退避）
