# 项目封面自动生成 - 完整文档

## 目录

1. [增强型后台任务调度器](#1-增强型后台任务调度器)
2. [项目封面自动生成功能](#2-项目封面自动生成功能)
3. [UI 实时反馈实现](#3-ui-实时反馈实现)
4. [封面路径问题修复](#4-封面路径问题修复)
5. [测试指南](#5-测试指南)
6. [完整实现总结](#6-完整实现总结)

---

## 1. 增强型后台任务调度器

### 概述

已将原有的简单调度器升级为增强型调度器，具有以下特性：

### 核心特性

#### 1.1 守护进程模式
- **监督线程（Supervisor）** - 后台常驻，持续监控所有任务
- **自动重启** - 任务崩溃时自动创建新线程重启
- **健康检查** - 每 2 秒检查一次所有任务状态

#### 1.2 独立线程执行
- **每个任务独立线程** - 任务之间完全隔离，互不影响
- **并发执行** - 所有任务可同时运行
- **线程标识** - 每个任务记录其 Worker ID

#### 1.3 任务崩溃自动重启
- **周期性任务** - 崩溃后自动重启，继续执行
- **一次性任务** - 崩溃后标记失败，不重启
- **崩溃计数** - 记录每个任务的崩溃次数
- **错误日志** - 完整记录异常堆栈信息

#### 1.4 任务状态追踪

**TaskState 枚举：**
- `IDLE` - 空闲（未启动）
- `RUNNING` - 运行中
- `CRASHED` - 崩溃
- `STOPPED` - 已停止

**TaskStatus 数据类：**
```python
@dataclass
class TaskStatus:
    name: str                    # 任务名称
    type: TaskType              # 任务类型
    state: TaskState            # 运行状态
    thread_id: Optional[int]    # 线程 ID
    start_time: Optional[datetime]  # 启动时间
    crash_count: int            # 崩溃次数
    last_error: Optional[str]   # 最后错误信息
```

### 架构设计

#### 三层架构

```
┌─────────────────────────────────────────┐
│   BackgroundTaskScheduler（调度器）      │
│   - 注册任务                             │
│   - 管理任务状态                         │
│   - 提供查询接口                         │
└──────────────┬──────────────────────────┘
               │
               ├─ 创建并管理
               ↓
┌─────────────────────────────────────────┐
│   _SupervisorThread（监督线程）          │
│   - 后台常驻（守护模式）                 │
│   - 每 2 秒检查任务状态                  │
│   - 启动新任务                           │
│   - 重启崩溃任务                         │
└──────────────┬──────────────────────────┘
               │
               ├─ 为每个任务创建
               ↓
┌─────────────────────────────────────────┐
│   _TaskWorker（任务工作线程）            │
│   - 在独立线程中执行任务                 │
│   - 捕获异常并发送信号                   │
│   - 周期性任务循环执行                   │
│   - 一次性任务执行一次                   │
└─────────────────────────────────────────┘
```

#### 信号机制

```python
# BackgroundTaskScheduler 发送的信号
task_started = Signal(str)           # 任务启动
task_finished = Signal(str)          # 任务完成
task_failed = Signal(str, str)       # 任务失败
task_crashed = Signal(str, str)      # 任务崩溃
task_restarted = Signal(str, int)    # 任务重启（崩溃次数）
```

### 工作流程

#### 周期性任务生命周期

```
启动应用
  ↓
注册任务（enabled=True）
  ↓
监督线程检测到任务空闲
  ↓
创建 _TaskWorker 线程
  ↓
执行 task.execute()
  ↓
等待 task.get_interval() 秒
  ↓
再次执行 task.execute()
  ↓
（循环执行，直到 task.should_continue() 返回 False）
  ↓
【如果崩溃】→ 监督线程检测 → 自动重启 → 继续执行
```

#### 一次性任务生命周期

```
应用启动 / 手动触发 trigger_task()
  ↓
task.enable() 设置为启用
  ↓
监督线程检测到任务启用且空闲
  ↓
创建 _TaskWorker 线程
  ↓
执行 task.execute()
  ↓
task.disable() 自动禁用
  ↓
任务完成
  ↓
【如果崩溃】→ 监督线程检测 → 标记失败 → 不重启
```

### 使用示例

```python
# 查询单个任务
status = scheduler.get_task_status("video_task_polling")
print(f"任务状态: {status.state.value}")
print(f"崩溃次数: {status.crash_count}")

# 查询所有任务
all_status = scheduler.get_all_status()
for name, status in all_status.items():
    print(f"{name}: {status.state.value}")

# 连接信号
scheduler.task_crashed.connect(on_task_crashed)
scheduler.task_restarted.connect(on_task_restarted)

def on_task_crashed(task_name: str, error: str):
    print(f"任务崩溃：{task_name}，错误：{error}")

def on_task_restarted(task_name: str, crash_count: int):
    print(f"任务重启：{task_name}（第 {crash_count} 次崩溃）")
```

### 日志示例

```
# 正常启动
INFO | 注册后台任务：video_task_polling（类型：periodic）
INFO | 注册后台任务：project_cover_generation（类型：one_time）
INFO | 后台任务调度器已启动（守护模式）
INFO | 监督线程进入主循环
DEBUG | 任务线程启动：video_task_polling (Worker ID: 1555059376704)
DEBUG | 任务线程启动：project_cover_generation (Worker ID: 1555059219072)

# 任务崩溃与重启
ERROR | 任务 video_task_polling 崩溃：division by zero
WARNING | 重启崩溃任务：video_task_polling（第 1 次崩溃）
DEBUG | 任务线程启动：video_task_polling (Worker ID: 1555060123456)

# 应用关闭
INFO | 正在停止后台任务调度器...
INFO | 正在停止任务：video_task_polling
INFO | 正在停止任务：project_cover_generation
INFO | 后台任务调度器已停止
```

### 配置参数

- **监督循环间隔**：2.0 秒（`_SupervisorThread.run()`）
- **任务停止超时**：3000 毫秒（`shutdown()` 中的 `worker.wait()`）

### 线程安全

- **QObject 信号** - 使用 Qt 信号机制实现线程间通信
- **独立线程** - 每个任务在独立线程中执行，互不干扰
- **状态同步** - 任务状态由调度器主线程管理，通过信号更新

### 对比原有调度器

| 特性 | 原调度器 | 增强型调度器 |
|------|---------|-------------|
| 任务执行 | 单线程顺序执行 | 多线程并发执行 |
| 崩溃处理 | 整个调度器崩溃 | 单个任务崩溃，其他任务不受影响 |
| 自动重启 | 不支持 | 周期性任务自动重启 |
| 状态追踪 | 简单状态 | 详细状态（崩溃次数、线程 ID、错误信息） |
| 守护模式 | 不支持 | 监督线程持续监控 |
| 健康检查 | 不支持 | 每 2 秒检查一次 |

### 故障排查

**任务频繁崩溃：**
```
grep "任务崩溃\|任务重启" "$LOCALAPPDATA/ai-video-gui/logs/app.log"
```
可能原因：任务代码 bug、资源不足、外部依赖不可用

**监督线程崩溃：**
- 已启动的任务继续运行
- 新任务无法启动
- 崩溃任务无法自动重启
- 监督线程会自动捕获异常并继续运行

### 未来优化

1. 最大重启次数限制 - 避免任务无限重启
2. 任务优先级 - 高优先级任务优先执行
3. 任务依赖关系 - 任务 A 完成后才启动任务 B
4. 协程支持 - 使用 asyncio 实现更轻量级的并发
5. 任务超时控制 - 超时自动终止任务
6. 资源限制 - 限制并发任务数量
7. 性能监控 - 任务执行时间、CPU/内存占用统计

---

## 2. 项目封面自动生成功能

### 功能概述

项目封面自动生成功能允许系统为有大纲但无封面的项目自动生成封面图。生成过程在后台执行，UI 上会显示实时的加载动画。

### 工作流程

1. **用户触发**：通过 QML 调用 `bridge.trigger_project_cover_generation()`
2. **任务扫描**：后台任务扫描所有项目，筛选出没有封面但有大纲的项目
3. **逐个生成**：
   - 发送 `cover_generation_started` 信号（项目 ID）
   - 使用大纲内容调用文生图 API 生成封面
   - 下载封面到项目隐藏文件夹（`.assets/cover_*.jpg`）
   - 更新项目的 `cover_image` 字段
   - 发送 `cover_generation_finished` 信号（项目 ID）
4. **UI 更新**：ProjectCard 显示转圈加载动画，生成完成后自动刷新显示封面

### UI 效果

**横屏视频（16:9、1:1 等）：**
```
┌──────────────────────────┐
│                          │
│     ⟳  (转圈动画)        │
│   生成封面中...          │
│                          │
└──────────────────────────┘
```

**竖屏视频（9:16）：**
```
┌────┬─────────────────────┐
│    │  项目名称           │
│ ⟳  │  9:16               │
│生成│  720P               │
│中  │  2026-07-30         │
└────┴─────────────────────┘
```

### 关键属性

**ProjectCard.qml：**
- `isGeneratingCover: bool` - 是否正在生成封面
- 当 `isGeneratingCover = true` 时：
  - 隐藏封面图和默认图标
  - 显示 `BusyIndicator`（转圈动画）
  - 显示提示文字（"生成封面中..." 或 "生成中..."）

### 使用方式

**手动触发（QML）：**
```qml
Button {
    text: "生成所有项目封面"
    onClicked: {
        bridge.trigger_project_cover_generation()
    }
}
```

**自动触发：**
- 应用启动时自动触发（默认行为）
- 项目创建后保存大纲时

**Python 代码触发：**
```python
scheduler = container.background_scheduler()
success = scheduler.trigger_task("project_cover_generation")
if success:
    logger.info("已触发项目封面生成任务")
```

### 封面生成策略

**Prompt 构建：**
```python
outline_summary = outline_content[:500]
prompt = f"为视频项目《{project_name}》生成封面图。项目大纲：{outline_summary}"
negative_prompt = "低质量，模糊，噪点，水印，文字"
```

**尺寸映射：**

| 宽高比 | 图片尺寸 | 说明 |
|--------|----------|------|
| 1:1 | 1280*1280 | 正方形 |
| 3:4 | 1104*1472 | 竖屏 |
| 4:3 | 1472*1104 | 横屏 |
| 9:16 | 960*1696 | 竖屏视频 |
| 16:9 | 1696*960 | 横屏视频（默认） |

**存储路径：**
```
workspace/projects/{project_id}/.assets/cover_{uuid}.jpg
```

### 注意事项

1. **API 配置**：需要在设置中配置文生图 Provider（如 `dashscope_image`）的 API Key
2. **大纲内容**：项目必须有非空的大纲内容才会生成封面
3. **网络依赖**：生成封面需要调用在线 API，网络不稳定可能导致失败
4. **生成时间**：单个封面生成通常需要 3-10 秒
5. **并发限制**：任务按顺序逐个生成，避免 API 限流

### 未来扩展

- 添加生成进度百分比（如 "2/5 正在生成..."）
- 支持手动为单个项目重新生成封面
- 支持自定义封面生成的 Prompt 模板
- 支持从本地上传封面图

---

## 3. UI 实时反馈实现

### 信号机制（Python → QML）

**1. 后台任务发送信号：**
```python
# ProjectCoverGenerationTask
self._signal_emitter.cover_generation_started.emit(project_id)
self._signal_emitter.cover_generation_finished.emit(project_id)
self._signal_emitter.cover_generation_failed.emit(project_id, error)
```

**2. Bridge 层转发信号：**
```python
# AppBridge
cover_generation_started = Signal(int)
cover_generation_finished = Signal(int)
cover_generation_failed = Signal(int, str)
```

**3. QML 监听并更新状态：**
```qml
property var generatingCoverIds: []  // 正在生成的项目 ID 列表

Connections {
    target: bridge
    function onCover_generation_started(projectId) {
        var ids = generatingCoverIds.slice()
        if (ids.indexOf(projectId) === -1) {
            ids.push(projectId)
            generatingCoverIds = ids
        }
    }
    function onCover_generation_finished(projectId) {
        var ids = generatingCoverIds.slice()
        var index = ids.indexOf(projectId)
        if (index !== -1) {
            ids.splice(index, 1)
            generatingCoverIds = ids
        }
        bridge.projects.load_projects()
    }
    function onCover_generation_failed(projectId, errorMessage) {
        var ids = generatingCoverIds.slice()
        var index = ids.indexOf(projectId)
        if (index !== -1) {
            ids.splice(index, 1)
            generatingCoverIds = ids
        }
    }
}
```

**4. ProjectCard 绑定状态：**
```qml
isGeneratingCover: generatingCoverIds.indexOf(projectId) !== -1

BusyIndicator { visible: isGeneratingCover }
Label { text: "生成封面中..."; visible: isGeneratingCover }
```

### 组合模式（解决元类冲突）

Python 的 `QObject` 有自己的元类，无法与 `BackgroundTask` 多继承。使用组合模式：

```python
class ProjectCoverGenerationTask(BackgroundTask):
    def __init__(self, ...):
        super().__init__(TaskType.ONE_TIME, "project_cover_generation")
        self._signal_emitter = _SignalEmitter()

    @property
    def signal_emitter(self) -> QObject:
        return self._signal_emitter

class _SignalEmitter(QObject):
    cover_generation_started = Signal(int)
    cover_generation_finished = Signal(int)
    cover_generation_failed = Signal(int, str)
```

### 设计亮点

1. **线程分离**：封面生成在后台线程，不阻塞 UI
2. **实时反馈**：用户可见每个项目的生成状态
3. **自动刷新**：生成完成自动更新显示，无需手动刷新
4. **响应式设计**：QML 属性绑定自动触发 UI 更新
5. **错误处理**：生成失败也会清除加载状态，避免卡死
6. **多项目支持**：可同时显示多个项目的生成进度

### 工作流程

```
用户触发 → 后台任务启动
    ↓
扫描项目（有大纲但无封面）
    ↓
逐个生成封面：
    ├─ 发送 started 信号 → UI 显示加载动画
    ├─ 调用文生图 API
    ├─ 下载图片到本地
    ├─ 更新数据库
    └─ 发送 finished 信号 → UI 刷新显示封面
```

---

## 4. 封面路径问题修复

### 问题描述

QML 中无法加载项目封面图片，报错：
```
QML QQuickImage: Cannot open: file:///projects/2/.assets/cover_c06451fe.jpg
QML QQuickImage: Cannot open: file:///projects/1/.assets/cover_7f9a7214.jpg
```

### 根本原因

1. **数据库存储相对路径**：`projects/1/.assets/cover_xxx.jpg`
2. **QML 需要绝对路径**：`file:///C:/Users/admin/.../workspace/projects/1/.assets/cover_xxx.jpg`
3. **Model 直接返回相对路径**：没有转换为绝对路径

### 解决方案

在 `ProjectListModel` 中将相对路径转换为绝对路径：

```python
class ProjectListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Project] = []
        workspace_root = paths.workspace_root()
        self._workspace_dir = paths.workspace_dir(workspace_root)

    def data(self, index, role=Qt.DisplayRole):
        if role == self.CoverPathRole:
            if item.cover_image:
                abs_path = os.path.join(self._workspace_dir, item.cover_image)
                return abs_path.replace('\\', '/')
            return ""
```

### 修改的文件

- `bridge/models/project_model.py` - 添加路径转换逻辑

### 验证结果

修复后，应用启动时不再出现图片加载错误：
- 没有 "Cannot open" 错误
- 项目封面正常显示
- 封面生成任务正常运行

### 设计说明

**为什么数据库存储相对路径？**
1. **可移植性**：workspace 目录可以迁移
2. **跨平台**：不依赖特定的绝对路径
3. **数据库小**：相对路径更短

**为什么在 Model 层转换？**
1. **单一职责**：Repository 只管数据存储
2. **视图适配**：Model 负责为 UI 层提供合适的数据格式
3. **性能**：只在需要显示时转换，不影响存储

---

## 5. 测试指南

### 自动触发说明

应用启动时会自动触发一次封面生成任务，系统会自动扫描所有项目并为符合条件的项目生成封面。

### 前提条件

1. **配置文生图 API**
   - 打开应用，点击左侧栏的设置图标
   - 在 Provider 配置中找到 `dashscope_image`
   - 填入阿里百炼的 API Key
   - 点击保存

2. **创建测试项目**
   - 点击右上角的 `+` 按钮创建一个新项目
   - 进入项目，创建故事大纲
   - 在大纲中输入一些内容（如："一个关于太空探险的科幻故事"）
   - 保存大纲

3. **返回项目列表**
   - 点击左上角返回按钮，回到项目网格页面

### 测试方式

#### 方式一：应用启动时自动触发（推荐）

**操作：**
1. 确保已配置 API Key 并创建了有大纲的项目
2. 启动应用
3. 系统会自动扫描并生成封面

**观察：**
- 应用启动后，打开项目网格页面
- 符合条件的项目会立即显示加载动画
- 查看日志确认任务已触发

#### 方式二：手动触发

在项目网格页面，标题栏右上角有两个按钮：
- **图片图标按钮**（左侧）：生成项目封面
- **加号按钮**（右侧）：新建项目

**操作：**
1. 鼠标悬停在图片图标按钮上，会显示 "生成项目封面" 提示
2. 点击该按钮

### 预期日志输出

**应用启动时：**
```
INFO | 触发一次性任务：project_cover_generation
INFO | 已触发启动时封面生成任务
INFO | 开始扫描项目并生成封面图
INFO | 共找到 X 个项目
INFO | 项目 XXX（ID: 1）没有封面，开始生成...
INFO | 提交图片生成任务，尺寸：1696*960，数量：1
INFO | 为项目 XXX（ID: 1）生成封面成功
INFO | 封面生成任务完成，成功：1，失败：0
```

**手动触发时：**
```
INFO | 已触发项目封面生成任务
INFO | 触发一次性任务：project_cover_generation
INFO | 开始扫描项目并生成封面图
INFO | 共找到 X 个项目
INFO | 项目 XXX（ID: 1）没有封面，跳过（需要大纲）
INFO | 为项目 XXX（ID: 1）生成封面...
INFO | 提交图片生成任务，尺寸：1696*960，数量：1
INFO | 为项目 XXX（ID: 1）生成封面成功
INFO | 封面生成任务完成，成功：1，失败：0
```

### 验证结果

生成完成后：
- **UI 自动更新**：转圈动画消失，ProjectCard 自动显示新生成的封面图
- **文件系统验证**：检查 `$LOCALAPPDATA/ai-video-gui/workspace/projects/1/.assets/` 下是否有 `cover_xxxxxxxx.jpg` 文件
- **数据库验证**：项目的 `cover_image` 字段已更新为相对路径

### 常见问题排查

**问题 1：点击按钮后没有任何反应**
- 原因：API Key 未配置或配置错误
- 解决：检查设置中是否配置了 `dashscope_image` 的 API Key

**问题 2：加载动画显示但一直不结束**
- 原因：API 调用失败或网络问题
- 解决：检查日志中的错误信息（`InvalidApiKey`、`Connection timeout`、`Rate limit exceeded`）

**问题 3：只有部分项目生成了封面**
- 原因：只有同时满足以下条件的项目才会生成封面：项目没有封面且项目有大纲
- 解决：为需要生成封面的项目添加大纲内容

**问题 4：生成的封面不符合预期**
- 原因：Prompt 构建使用了大纲的前 500 字符
- 解决：修改大纲，将关键描述放在前面

### 调试技巧

1. **开启详细日志**：修改 `main.py` 中的日志级别为 `DEBUG`
2. **监控信号连接**：在 `ProjectGridPage.qml` 中添加 `console.log` 调试输出
3. **手动触发单个项目**：在 Python 代码中直接调用 `task._generate_cover_for_project()`

---

## 6. 完整实现总结

### 所有功能已完成

#### 增强型后台任务调度器
- 守护进程模式 - 监督线程后台常驻
- 独立线程执行 - 每个任务在独立线程中运行
- 任务崩溃自动重启 - 周期性任务崩溃后自动重启
- 详细状态追踪 - 记录线程 ID、崩溃次数、错误信息

#### 项目封面自动生成
- 扫描项目并生成封面（有大纲但无封面）
- 使用文生图 API 根据大纲生成
- 自动下载到项目隐藏文件夹（`.assets/`）
- 应用启动时自动触发
- 手动触发（UI 按钮）

#### UI 实时反馈
- ProjectCard 显示转圈加载动画
- 提示文字（"生成封面中..."）
- 生成完成自动刷新显示
- 支持多项目同时显示生成状态

#### 视频轮询服务重构
- 从独立服务改造为可调度的周期性任务
- 在独立线程中运行，不阻塞其他任务
- 保留所有原有功能（状态轮询、下载、入库）

#### 问题修复
- QML 信号处理器参数注入警告已修复
- 封面图片路径问题已修复（相对路径 → 绝对路径）
- 线程 ID 获取问题已修复（`currentThreadId` → `id(worker)`）
- 元类冲突 - 使用组合模式（持有 QObject）而非多继承

### 关键设计

#### 1. 守护模式
监督线程持续运行，每 2 秒检查所有任务：
- 周期性任务：崩溃 → 自动重启
- 一次性任务：启用且空闲 → 启动执行

#### 2. 独立线程隔离
每个任务在独立的 `_TaskWorker` 线程中执行：
- 任务 A 崩溃不影响任务 B
- 任务并发执行，互不阻塞
- 异常捕获并记录，发送崩溃信号

#### 3. 信号驱动 UI
```
后台任务（线程 A）
    ↓ 信号
_SignalEmitter（QObject）
    ↓ 信号
AppBridge
    ↓ 信号
QML（主线程）
    ↓ 属性绑定
UI 自动更新
```

#### 4. 路径转换
```
数据库：相对路径 "projects/1/.assets/cover.jpg"
    ↓ ProjectListModel.data()
QML：绝对路径 "C:/Users/.../workspace/projects/1/.assets/cover.jpg"
```

### 工作流程

#### 应用启动
```
1. 初始化 DI 容器
2. 创建调度器
3. 注册任务（video_polling, project_cover_generation）
4. 启动调度器 → 监督线程启动
5. 触发封面生成任务
6. 监督线程检测到任务 → 创建 TaskWorker
7. 任务开始执行
```

#### 封面生成流程
```
1. 触发任务（启动时 / 手动点击按钮）
2. task.enable() 启用任务
3. 监督线程检测 → 创建 TaskWorker
4. 扫描所有项目
5. 对于每个符合条件的项目：
   - 发送 cover_generation_started 信号
   - UI 显示加载动画
   - 调用文生图 API
   - 下载图片到本地
   - 更新数据库
   - 发送 cover_generation_finished 信号
   - UI 刷新显示封面
6. 任务完成，自动禁用
```

#### 任务崩溃处理
```
1. TaskWorker 执行任务时发生未捕获异常
2. 捕获异常，发送 crashed_signal
3. 调度器更新状态：state = CRASHED
4. 监督线程检测到崩溃（下一次循环）
5. 周期性任务 → 自动重启（创建新 TaskWorker）
6. 一次性任务 → 标记失败，不重启
```

### 性能特点

- **并发执行**：视频轮询和封面生成同时运行
- **低延迟**：监督线程 2 秒检查一次
- **资源隔离**：每个任务独立线程，内存隔离
- **容错性**：单个任务崩溃不影响其他任务

### 对比原始需求

| 需求 | 状态 |
|------|------|
| 后台任务调度独立化 | 完成 |
| 主调度器常驻，挂掉就重启 | 监督线程守护模式 |
| 每个任务独立线程执行 | _TaskWorker 独立线程 |
| 任务崩溃自动重启 | 周期性任务自动重启 |
| 支持协程/虚拟线程 | 当前使用 QThread，可扩展 |
| 项目封面自动生成 | 完成 |
| UI 实时加载动画 | 完成 |
| 启动时自动触发 | 完成 |

### 新增/修改的文件

#### 核心功能
1. `service/background/enhanced_scheduler.py` - 增强型调度器
2. `service/background/task_base.py` - 任务抽象基类
3. `service/background/video_polling_task.py` - 视频轮询任务（重构）
4. `service/background/project_cover_task.py` - 封面生成任务
5. `main.py` - 使用增强型调度器 + 启动时触发

#### Bridge & UI
6. `bridge/app_bridge.py` - 封面生成信号转发
7. `bridge/models/project_model.py` - 路径转换修复
8. `qml/components/MainPanel.qml` - 生成封面按钮
9. `qml/components/ProjectCard.qml` - 加载动画
10. `qml/pages/ProjectGridPage.qml` - 信号监听 + 参数修复

#### 配置
11. `di/containers.py` - 注册增强型调度器
12. `storage/repositories/project_repository.py` - 更新封面方法

### 验证结果

应用启动日志：
```
INFO | 后台任务调度器已启动（守护模式）
INFO | 已触发启动时封面生成任务
INFO | 监督线程进入主循环
DEBUG | 任务线程启动：video_task_polling (Worker ID: 1555059376704)
DEBUG | 任务线程启动：project_cover_generation (Worker ID: 1555059219072)
INFO | 开始扫描项目并生成封面图
INFO | 共找到 2 个项目
DEBUG | 项目 xxx（ID: 1）已有封面，跳过
DEBUG | 项目 xxx（ID: 2）已有封面，跳过
INFO | 封面生成任务完成，成功：0，失败：0
```

无错误运行：
- 没有 QML 警告
- 没有图片加载错误
- 任务线程正常运行
- 监督线程正常监控

### 未来优化建议

1. **进度显示**：显示 "2/5 正在生成..."
2. **单项操作**：为单个项目添加"重新生成封面"按钮
3. **自定义 Prompt**：允许用户自定义封面生成提示词
4. **手动上传**：支持从本地上传封面图
5. **预览编辑**：生成后可预览并选择是否保留
6. **批量操作**：添加"全选"功能，批量生成或删除封面
7. **缓存机制**：避免重复生成相同内容的封面