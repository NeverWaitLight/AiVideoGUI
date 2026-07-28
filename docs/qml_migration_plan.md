## 从 PyQt6 Widgets 迁移到 PySide6 QML/Qt Quick

本文档描述将 ai-video-gui 前端 UI 从 PyQt6 + PyQt6-Fluent-Widgets 全面迁移到 PySide6 + QML/Qt Quick + Qt Quick Controls 的实施方案。

---

## 现状分析

### UI 文件清单

| 文件 | 行数 | 主要类 | 职责 |
|------|------|--------|------|
| `main_window.py` | 2127 | `MainWindow`, `_BatchGenerationController`, 5个内联Worker | 主窗口、服务编排、批量生成 |
| `storyboard_editor.py` | 1104 | `StoryboardEditor`, `StoryboardCard`, `StoryboardDetailEditor` | 分镜编辑（列表+详情+批量操作） |
| `character_page.py` | 774 | `CharacterPage`, `CharacterCard`, `CharacterDetailPage` | 角色管理（列表+详情+历史） |
| `screenplay_editor.py` | 656 | `ScreenplayEditor`, `SceneCard`, `SceneDetailEditor` | 剧本编辑（场次列表+场次编辑） |
| `project_page.py` | 654 | `ProjectPage`, `_ProjectRow`, `_ConversationRow`, `_ProjectDialog` | 项目管理三栏布局 |
| `video_player_page.py` | 636 | `VideoPlayerPage` | 视频播放器（双QMediaPlayer无缝切换） |
| `media_library.py` | 576 | `MediaLibrary`, `_MediaCard`, `_EmptyState` | 素材库（网格+过滤+搜索） |
| `widgets.py` | 552 | `MessageBubble`, `VideoStatusCard`, `SpinnerOverlay`, `AlertDialog` | 公共组件 |
| `project_grid_page.py` | 537 | `ProjectGridPage`, `ProjectCard`, `ProjectDialog` | 项目网格卡片视图 |
| `story_outline_editor.py` | 523 | `StoryOutlineEditor`, `StoryOutlineChatPanel`, `OptimizeWorker` | 故事大纲编辑+AI对话优化 |
| `timeline_widget.py` | 466 | `TimelineWidget`, `TimelinePreview` | 视频时间轴（自定义QPainter绘制） |
| `settings_dialog.py` | 397 | `SettingsDialog` | 设置对话框（Provider配置） |
| `chat_area.py` | 302 | `ChatArea`, `ParameterPanel` | 聊天区域（消息流+参数面板） |
| `sidebar.py` | 218 | `Sidebar`, `_ConversationRow` | 左侧边栏（对话列表） |
| `project_detail_page.py` | 211 | `ProjectDetailPage`, `ModuleCard` | 项目详情页（模块入口网格） |
| `page_header.py` | 132 | `PageHeader`, `PageTitleBar` | 统一页头（返回按钮+标题） |
| `tab_bar.py` | 108 | `TabBar` | 垂直Tab栏（模式切换） |
| `styles.py` | 71 | （模块级函数和常量） | 全局样式和颜色常量 |
| `__init__.py` | 0 | — | 空文件 |
| **合计** | **~9,252** | | |

### 外部依赖

**需移除：**
- `pyqt6 >= 6.11.0` — Qt 绑定库
- `pyqt6-fluent-widgets >= 1.11.2` — Fluent Design 组件库
- `qframelesswindow`（间接依赖）— 无边框窗口

**需新增：**
- `PySide6 >= 6.7` — Qt for Python 绑定（LGPL 协议）

### PyQt6-Fluent-Widgets 组件使用统计

| 组件 | 使用文件 |
|------|----------|
| `PrimaryPushButton` | chat_area, sidebar, settings_dialog, widgets, project_page, project_grid_page, story_outline_editor, screenplay_editor, storyboard_editor, character_page, media_library, video_player_page |
| `PushButton` | sidebar, settings_dialog, widgets, project_page, project_grid_page, story_outline_editor, screenplay_editor, storyboard_editor, character_page, media_library, video_player_page, main_window |
| `ToolButton` | sidebar, page_header, tab_bar, video_player_page, project_page, project_grid_page |
| `FluentIcon` | sidebar, page_header, tab_bar, video_player_page, project_page, project_grid_page, project_detail_page, story_outline_editor, screenplay_editor, storyboard_editor, character_page, media_library |
| `ComboBox` | chat_area, settings_dialog, storyboard_editor, media_library |
| `LineEdit` | settings_dialog, project_page, project_grid_page, storyboard_editor, character_page, media_library |
| `TextEdit` | chat_area, story_outline_editor, storyboard_editor, character_page, main_window |
| `CardWidget` | project_grid_page, project_detail_page, screenplay_editor, storyboard_editor, character_page |
| `ListWidget` | sidebar, project_page, storyboard_editor, character_page |
| `SwitchButton` | chat_area |
| `CheckBox` | storyboard_editor, character_page |
| `DoubleSpinBox` | storyboard_editor |
| `TitleLabel` | storyboard_editor, character_page, video_player_page |
| `IndeterminateProgressBar` | widgets, main_window |
| `ProgressBar` | widgets, main_window |
| `ProgressRing` | main_window |
| `RoundMenu` + `Action` | sidebar, media_library |
| `MessageBox` | media_library |
| `Theme` / `setTheme` / `setThemeColor` | styles |

### 信号系统现状

**Service 层信号（保持逻辑不变，仅替换绑定库）：**

| 类 | 信号 | 签名 |
|----|------|------|
| `TaskPollingService` | `status_changed` | `(str, str)` |
| `TaskPollingService` | `download_progress` | `(str, int, int)` |
| `TaskPollingService` | `task_finished` | `(str, str, int)` |
| `TaskPollingService` | `task_failed` | `(str, str)` |
| `ChatService` | `title_ready` | `(str, str)` |
| `ChatService` | `title_failed` | `(str, str)` |

**UI 层信号（将在 Bridge 层重新定义）：**

| 来源 | 信号 | 签名 |
|------|------|------|
| `TabBar` | `tab_changed` | `(int)` |
| `TabBar` | `library_clicked` / `settings_clicked` | `()` |
| `Sidebar` | `new_conversation_clicked` | `()` |
| `Sidebar` | `conversation_selected` / `conversation_deleted` | `(str)` |
| `ChatArea` | `message_sent` | `(str, dict)` |
| `ProjectGridPage` | `project_selected` | `(int)` |
| `ProjectDetailPage` | `module_selected` | `(int, str)` |
| `ProjectDetailPage` | `back_clicked` | `()` |
| `StoryOutlineEditor` | `next_step_clicked` | `(str)` |
| `ScreenplayEditor` | `generate_storyboard_clicked` | `(int)` |
| `StoryboardEditor` | `video_generation_requested` | `(int, int, int, str, int, str)` |
| `StoryboardEditor` | `batch_video_generation_requested` | `(list)` |
| `StoryboardEditor` | `design_image_generation_requested` | `(int, int)` |
| `CharacterPage` | `design_image_generation_requested` | `(str, int)` |
| `MediaLibrary` | `jump_to_conversation_requested` | `(str, str)` |
| `VideoStatusCard` | `open_folder_clicked` | `(str)` |
| `VideoPlayerPage` | `back_clicked` | `()` |
| 各编辑器页面 | `back_clicked` | `()` |

**MainWindow 内联 Worker 类（需迁移到 Bridge 层）：**

| Worker | 所在方法 | 信号 |
|--------|----------|------|
| `_BatchGenerationController` | 类级 | `progress`, `all_done`, `terminated` |
| `ScriptGenerateWorker` | `_on_generate_storyboard()` | `finished(str, list)`, `failed(str)` |
| `StoryboardGenerateWorker` | `_on_preview_prompt_request()` | `finished(dict)`, `failed(str)` |
| `DesignImageWorker` | `_on_shot_video_generation()` 等 | `finished(str)`, `failed(str)`, `progress_update(str)` |
| `BatchDesignImageWorker` | `_on_batch_generate_design_images()` | `progress_update`, `finished`, `failed` |
| `CharacterDesignImageWorker` | `_on_generate_character_design_image()` | `finished(str)`, `failed(str)`, `progress_update(str)` |

---

## 技术选型

### Qt 绑定：PySide6

**选择理由：**
- QML 集成更成熟 — 支持 `qmlregister`、`QML_ELEMENT`、`QML_NAMED_ELEMENT` 等宏
- 原生 `QtQml` 模块支持 QML 类型注册
- LGPL 协议，比 PyQt6 的 GPL/商用双协议更灵活
- 与 PyQt6 API 高度相似，Service 层迁移成本可控

**关键差异（需全局替换）：**
- `pyqtSignal` → `Signal`
- `pyqtSlot` → `Slot`
- `pyqtProperty` → `Property`
- `PyQt6.QtCore.Qt.xxx` 枚举 → `PySide6.QtCore.Qt.xxx`（部分枚举路径不同）
- `QApplication.exec()` 在 PySide6 中同样可用

### UI 框架：Qt Quick + Qt Quick Controls

**使用的 Qt Quick 模块：**
- `QtQuick` — 基础类型（Item, Rectangle, Text, Image, MouseArea, Loader 等）
- `QtQuick.Controls` — 控件（Button, TextField, TextArea, ComboBox, CheckBox, Switch, ProgressBar, Dialog, Menu 等）
- `QtQuick.Layouts` — 布局（RowLayout, ColumnLayout, GridLayout, StackLayout）
- `QtMultimedia` — 视频播放（MediaPlayer, VideoOutput）
- `QtQuick.Dialogs` — 系统对话框（FileDialog, FolderDialog, MessageDialog）

### 桥接方式：QAbstractListModel + Context Property

**架构：**

```
┌─────────────────────────────────────────┐
│  QML Layer (qml/)                       │
│  ├── main.qml                           │
│  ├── pages/ (页面级组件)                  │
│  ├── components/ (可复用组件)              │
│  └── dialogs/ (对话框)                    │
├─────────────────────────────────────────┤
│  Bridge Layer (bridge/)                  │
│  ├── app_bridge.py (统一入口 QObject)     │
│  ├── models/ (QAbstractListModel 子类)   │
│  └── workers.py (QThread Worker 类)      │
├─────────────────────────────────────────┤
│  Service Layer (service/) — 不变         │
│  DI Container (di/) — 微调              │
│  Storage Layer (storage/) — 不变         │
│  Provider Layer (providers/) — 不变      │
└─────────────────────────────────────────┘
```

**数据流向：**
- QML → Bridge：QML 调用 `AppBridge` 的 `Slot` 方法
- Bridge → Service：Bridge 调用 Service 方法，获取数据
- Service → Bridge：Service 通过 Signal 通知 Bridge
- Bridge → QML：Bridge 通过 `Property` / `Signal` / `ListModel` 通知 QML 更新

---

## 新项目目录结构

```
ai-video-gui/
├── main.py                      # 入口（改造为 QQmlApplicationEngine）
├── pyproject.toml               # 更新依赖
├── bridge/                      # Python ↔ QML 桥接层（新增）
│   ├── __init__.py
│   ├── app_bridge.py            # AppBridge 统一入口 QObject
│   ├── conversation_bridge.py   # 对话相关桥接
│   ├── project_bridge.py        # 项目相关桥接
│   ├── media_bridge.py          # 素材库桥接
│   ├── storyboard_bridge.py     # 分镜桥接
│   ├── character_bridge.py      # 角色桥接
│   ├── settings_bridge.py       # 设置桥接
│   ├── video_player_bridge.py   # 视频播放桥接
│   ├── models/                  # QAbstractListModel 子类
│   │   ├── __init__.py
│   │   ├── conversation_model.py
│   │   ├── message_model.py
│   │   ├── project_model.py
│   │   ├── scene_model.py
│   │   ├── storyboard_model.py
│   │   ├── character_model.py
│   │   ├── media_file_model.py
│   │   └── history_model.py
│   └── workers.py               # 所有 QThread Worker 类（从 main_window.py 迁移）
├── qml/                         # QML 前端（新增）
│   ├── main.qml                 # 根组件（ApplicationWindow）
│   ├── Theme.qml                # 全局主题/样式常量（单例）
│   ├── pages/                   # 页面级组件
│   │   ├── DirectModePage.qml   # 直接生成模式（sidebar + chat）
│   │   ├── ProjectModePage.qml  # 项目管理模式容器
│   │   ├── ProjectGridPage.qml  # 项目网格
│   │   ├── ProjectDetailPage.qml # 项目详情（模块入口）
│   │   ├── StoryOutlinePage.qml # 故事大纲编辑
│   │   ├── ScreenplayPage.qml   # 剧本编辑
│   │   ├── StoryboardPage.qml   # 分镜编辑
│   │   ├── CharacterPage.qml    # 角色管理
│   │   ├── MediaLibraryPage.qml # 素材库
│   │   ├── VideoPlayerPage.qml  # 视频播放
│   │   └── ProjectChatPage.qml  # 项目对话
│   ├── components/              # 可复用组件
│   │   ├── TabBar.qml           # 垂直Tab栏
│   │   ├── Sidebar.qml          # 侧边栏（对话列表）
│   │   ├── ChatArea.qml         # 聊天区域
│   │   ├── MessageBubble.qml    # 消息气泡
│   │   ├── VideoStatusCard.qml  # 视频状态卡片
│   │   ├── ParameterPanel.qml   # 参数面板
│   │   ├── PageHeader.qml       # 页头（返回+标题）
│   │   ├── ProjectCard.qml      # 项目卡片
│   │   ├── SceneCard.qml        # 场次卡片
│   │   ├── StoryboardCard.qml   # 分镜卡片
│   │   ├── CharacterCard.qml    # 角色卡片
│   │   ├── MediaCard.qml        # 素材卡片
│   │   ├── TimelineWidget.qml   # 视频时间轴
│   │   ├── SpinnerOverlay.qml   # 加载动画
│   │   └── EmptyState.qml       # 空状态占位
│   ├── dialogs/                 # 对话框
│   │   ├── SettingsDialog.qml   # 设置对话框
│   │   ├── ProjectDialog.qml    # 项目创建/编辑
│   │   ├── AlertDialog.qml      # 提示对话框
│   │   ├── HistoryDialog.qml    # 历史版本对话框
│   │   └── ConfirmDialog.qml    # 确认对话框
│   └── assets/                  # 静态资源
│       ├── default_project_cover.svg
│       └── default_video_cover.png
├── config/                      # 不变
├── di/                          # 微调（pyqtSignal → Signal）
├── models/                      # 不变
├── providers/                   # 不变
├── service/                     # 微调（pyqtSignal → Signal）
├── storage/                     # 不变
└── utils/                       # 不变
```

---

## Python Bridge 层接口设计

### AppBridge — 统一入口

`AppBridge` 是暴露给 QML 的唯一顶层对象，通过 `setContextProperty("bridge", app_bridge)` 注入。内部持有所有子 Bridge 实例。

```python
class AppBridge(QObject):
    # ── 全局信号（QML 中通过 Connections 监听）──
    
    # 轮询服务信号转发
    task_status_changed = Signal(str, str)        # task_id, status
    task_download_progress = Signal(str, int, int) # task_id, received, total
    task_finished = Signal(str, str, int)          # message_id, local_path, storyboard_id
    task_failed = Signal(str, str)                 # message_id, error
    
    # 对话服务信号转发
    title_ready = Signal(str, str)                 # conv_id, title
    
    # 批量生成信号
    batch_progress = Signal(int, int, str)         # submitted, total, status
    batch_done = Signal(int, int)                  # success, failed
    batch_terminated = Signal(int, int)            # success, failed
    
    # AI Worker 信号
    script_generated = Signal(str, list)           # script_id, scenes
    script_failed = Signal(str)                    # error
    storyboard_generated = Signal(dict)            # storyboard_data
    design_image_ready = Signal(str, str)          # target_id, image_path
    design_image_progress = Signal(str)            # progress_text
    
    # ── 导航信号 ──
    navigate_requested = Signal(str, dict)         # page_name, params
    
    # ── 属性 ──
    @Property(ConversationBridge)
    def conversations(self): ...
    
    @Property(ProjectBridge)
    def projects(self): ...
    
    @Property(MediaBridge)
    def media(self): ...
    
    @Property(StoryboardBridge)
    def storyboard(self): ...
    
    @Property(CharacterBridge)
    def characters(self): ...
    
    @Property(SettingsBridge)
    def settings(self): ...
    
    @Property(VideoPlayerBridge)
    def videoPlayer(self): ...
```

### ConversationBridge

```python
class ConversationBridge(QObject):
    # 列表模型
    @Property(ConversationListModel)
    def model(self): ...
    
    @Property(MessageListModel)
    def messages(self): ...
    
    # 操作
    @Slot()
    def create_new(self): ...
    
    @Slot(str)
    def select(self, conv_id): ...
    
    @Slot(str)
    def delete(self, conv_id): ...
    
    @Slot(str, QJsonObject)
    def send_message(self, text, params): ...
    
    # 信号
    conversation_created = Signal(str)     # conv_id
    message_added = Signal(QJsonObject)    # message_data
    conversation_list_changed = Signal()
```

### ProjectBridge

```python
class ProjectBridge(QObject):
    @Property(ProjectListModel)
    def gridModel(self): ...
    
    @Property(ProjectListModel)
    def listModel(self): ...
    
    @Slot(int)
    def select_project(self, project_id): ...
    
    @Slot(str, str, str, str)
    def create_project(self, name, resolution, ratio, cover): ...
    
    @Slot(int, str, str, str, str)
    def update_project(self, project_id, name, resolution, ratio, cover): ...
    
    @Slot(int)
    def delete_project(self, project_id): ...
    
    @Slot(int, str)
    def open_module(self, project_id, module_name): ...
    
    project_created = Signal(int)
    project_updated = Signal(int)
    project_deleted = Signal(int)
```

### StoryboardBridge

```python
class StoryboardBridge(QObject):
    @Property(StoryboardListModel)
    def model(self): ...
    
    @Slot(int)
    def load_for_project(self, project_id): ...
    
    @Slot(int, QJsonObject)
    def update_shot(self, shot_id, data): ...
    
    @Slot(int, int)
    def preview_prompt(self, storyboard_id, project_id): ...
    
    @Slot(int, int, int, str, int, str)
    def generate_video(self, shot_id, scene, shot, prompt, project_id, design_image): ...
    
    @Slot(list)
    def batch_generate_videos(self, shot_list): ...
    
    @Slot(int, int)
    def generate_design_image(self, storyboard_id, project_id): ...
    
    @Slot(list)
    def batch_generate_design_images(self, shot_list): ...
    
    data_changed = Signal()
```

### QAbstractListModel 示例 — ConversationListModel

```python
class ConversationListModel(QAbstractListModel):
    """对话列表模型，供 QML ListView 使用。"""
    
    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    TimeRole = Qt.UserRole + 3
    
    def roleNames(self):
        return {
            self.IdRole: b"convId",
            self.TitleRole: b"title",
            self.TimeRole: b"timeText",
        }
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._data[index.row()]
        if role == self.IdRole:
            return item.id
        elif role == self.TitleRole:
            return item.title
        elif role == self.TimeRole:
            return item.created_at.strftime("%Y-%m-%d %H:%M")
        return None
    
    def refresh(self):
        """从 Repository 重新加载数据。"""
        self.beginResetModel()
        self._data = self._repo.list_all(is_hidden=False)
        self.endResetModel()
```

### 其他 ListModel 定义

| Model | 角色 | 数据源 |
|-------|------|--------|
| `ConversationListModel` | convId, title, timeText | ConversationRepository |
| `MessageListModel` | msgId, role, content, status, localPath, timestamp, duration, width, height | MessageRepository |
| `ProjectListModel` | projectId, name, resolution, ratio, coverPath, createdAt | ProjectRepository |
| `SceneListModel` | sceneId, sceneNumber, location, timeOfDay, content | SceneRepository (by script_id) |
| `StoryboardListModel` | shotId, sceneNumber, shotNumber, shotSize, cameraMovement, visualContent, dialogue, duration, designImagePath | StoryboardRepository (by project_id) |
| `CharacterListModel` | characterId, name, refCode, description, designImagePath | CharacterRepository (by project_id) |
| `MediaFileListModel` | fileId, fileName, fileType, filePath, thumbnailPath, duration, width, height | MediaRepository |
| `HistoryListModel` | historyId, createdAt, previewText | *_history Repository |

---

## 逐页面迁移映射

### 导航框架

| 现有 Python 组件 | QML 替代 | 说明 |
|------------------|----------|------|
| `TabBar` | `TabBar.qml` | 垂直按钮组，使用 `Button` + `ButtonGroup` |
| `PageHeader` | `PageHeader.qml` | `RowLayout` + `ToolButton` + `Label` |
| `MainWindow` 的 hide/show 页面切换 | `StackView` 或 `StackLayout` | QML 原生导航栈 |
| `QSplitter` 三栏布局 | `SplitView` (Qt Quick Controls) | 原生支持拖拽分割 |

### 直接生成模式

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `Sidebar` | `Sidebar.qml` | `ListView` + `Button`（新建）+ `Delegate`（对话行） |
| `ChatArea` | `ChatArea.qml` | `ListView`（消息流）+ `TextArea`（输入）+ 内嵌 `ParameterPanel` |
| `ParameterPanel` | `ParameterPanel.qml` | `ComboBox`（比例/分辨率）+ `SpinBox`（时长）+ `Switch`（扩展/水印） |
| `MessageBubble` | `MessageBubble.qml` | `Rectangle` + `Text` + `Label`（气泡样式） |
| `VideoStatusCard` | `VideoStatusCard.qml` | `StackLayout`（generating/downloading/completed/failed 状态） + `ProgressBar` |

### 项目管理模式

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `ProjectGridPage` | `ProjectGridPage.qml` | `GridView` + `ProjectCard` delegate |
| `ProjectCard` | `ProjectCard.qml` | `Pane` + `Image` + `Label` + `MenuButton` |
| `ProjectDetailPage` | `ProjectDetailPage.qml` | `GridLayout` + `ModuleCard` delegate |
| `ProjectPage` | `ProjectChatPage.qml` | `SplitView`（项目列表 + 对话列表 + 聊天区域） |

### 编辑页面

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `StoryOutlineEditor` | `StoryOutlinePage.qml` | `SplitView` + `TextArea` + 侧边 `ChatPanel`（`ListView` + `TextArea`） |
| `ScreenplayEditor` | `ScreenplayPage.qml` | `ListView`（场次列表）+ `SceneCard` delegate + `SceneDetailEditor` panel |
| `SceneCard` | `SceneCard.qml` | `Pane` + `Label` + 状态指示 |
| `SceneDetailEditor` | 内嵌于 `ScreenplayPage.qml` | `FormLayout` 用 `ColumnLayout` + `TextField` / `TextArea` / `ComboBox` |
| `StoryboardEditor` | `StoryboardPage.qml` | `ListView`（分镜列表）+ `StoryboardCard` delegate + 详情 panel |
| `StoryboardCard` | `StoryboardCard.qml` | `Pane` + `CheckBox` + `Image` + `Label` + `Button` |
| `StoryboardDetailEditor` | 内嵌于 `StoryboardPage.qml` | `ScrollView` + `ColumnLayout` + `ComboBox`/`SpinBox`/`TextArea`/`TextField` |
| `CharacterPage` | `CharacterPage.qml` | `StackLayout`（list ↔ detail） + `ListView` + `CharacterCard` delegate |
| `CharacterCard` | `CharacterCard.qml` | `Pane` + `Image` + `Label` + `CheckBox` |

### 素材库

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `MediaLibrary` | `MediaLibraryPage.qml` | `GridView` + `MediaCard` delegate + `ComboBox`（过滤）+ `TextField`（搜索） |
| `MediaCard` | `MediaCard.qml` | `Pane` + `Image`（缩略图）+ `Label` + `Menu`（右键菜单） |

### 视频播放

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `VideoPlayerPage` | `VideoPlayerPage.qml` | `VideoOutput` + `MediaPlayer` + `Slider`（进度条）+ `ToolButton`（控制按钮） |
| `TimelineWidget` | `TimelineWidget.qml` | `Canvas` 或自定义 `Item`（时间轴绘制） |

### 对话框

| 现有 Python 组件 | QML 替代 | Qt Quick Controls 组件 |
|------------------|----------|----------------------|
| `SettingsDialog` | `SettingsDialog.qml` | `Dialog` + `TabBar`（分类） + `StackLayout`（内容页） |
| `ProjectDialog` | `ProjectDialog.qml` | `Dialog` + `FormLayout`（`TextField` + `ComboBox` + `Button`） |
| `AlertDialog` | `AlertDialog.qml` | `Dialog`（info/warning/error 变体） |
| `HistoryDialog` | `HistoryDialog.qml` | `Dialog` + `ListView` + `Button`（恢复） |
| `_ConfirmDelete` | `ConfirmDialog.qml` | `Dialog` + `Label` + `Button`（确认/取消） |

### 自定义绘制组件

| 现有 Python 组件 | QML 替代 | 方案 |
|------------------|----------|------|
| `SpinnerOverlay` | `SpinnerOverlay.qml` | `Canvas` + `Timer` 旋转动画，或 `AnimatedRotation` + 圆弧 Path |
| `TimelineWidget` | `TimelineWidget.qml` | `Canvas` 绘制刻度/片段/播放头，`MouseArea` 处理拖拽和 seek |

---

## Service 层适配

### 全局替换：pyqtSignal → Signal

**影响文件：**

| 文件 | 替换内容 |
|------|----------|
| `service/task_polling_service.py` | `from PyQt6.QtCore import QObject, QThread, pyqtSignal` → `from PySide6.QtCore import QObject, QThread, Signal`；`pyqtSignal(...)` → `Signal(...)` |
| `service/chat_service.py` | 同上 |

**替换规则：**
- `from PyQt6.QtCore import ...` → `from PySide6.QtCore import ...`
- `pyqtSignal` → `Signal`
- `pyqtSlot` → `Slot`
- `QThread` API 保持一致（`start()`, `quit()`, `wait()`, `isRunning()`）

### Worker 类迁移

`main_window.py` 中的 5 个内联 Worker 类迁移到 `bridge/workers.py`，改为 PySide6 语法：

```python
# 替换前 (PyQt6)
class ScriptGenerateWorker(QThread):
    finished = pyqtSignal(str, list)
    failed = pyqtSignal(str)

# 替换后 (PySide6)
class ScriptGenerateWorker(QThread):
    finished = Signal(str, list)
    failed = Signal(str)
```

`_BatchGenerationController` 也迁移到 `bridge/workers.py`，保持其 QObject 基类和信号驱动模式。

### DI 容器调整

`di/containers.py` 本身不依赖 Qt（使用 `dependency-injector` 库），无需修改。但 `ApplicationContainer` 需要新增 Bridge 层的 Provider：

```python
# 新增到 containers.py
from bridge.app_bridge import AppBridge

class ApplicationContainer(containers.DeclarativeContainer):
    # ... 现有 providers ...
    
    # Bridge 层（新增）
    app_bridge = providers.Singleton(
        AppBridge,
        container=providers.Self,
    )
```

### main.py 改造

```python
# 替换前
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

# 替换后
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from di import ApplicationContainer

app = QApplication(sys.argv)

# 初始化容器和 Bridge
container = ApplicationContainer()
# ... 配置 container ...
bridge = container.app_bridge()

# 加载 QML
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("bridge", bridge)
engine.load("qml/main.qml")

sys.exit(app.exec())
```

---

## pyproject.toml 依赖变更

**移除：**
```
pyqt6 >= 6.11.0
pyqt6-fluent-widgets >= 1.11.2
```

**新增：**
```
PySide6 >= 6.7
```

**注意：** `qframelesswindow` 是 `pyqt6-fluent-widgets` 的间接依赖，移除后者时自动移除。

**执行命令：**
```bash
uv remove pyqt6 pyqt6-fluent-widgets
uv add PySide6
```

---

## 全局 import 替换清单

以下替换需在所有非 UI 的 Python 文件中执行（UI 文件将被删除重建）：

| 原始 import | 替换为 |
|-------------|--------|
| `from PyQt6.QtCore import ...` | `from PySide6.QtCore import ...` |
| `from PyQt6.QtWidgets import ...` | `from PySide6.QtWidgets import ...` |
| `from PyQt6.QtGui import ...` | `from PySide6.QtGui import ...` |
| `from PyQt6.QtMultimedia import ...` | `from PySide6.QtMultimedia import ...` |
| `from PyQt6.QtMultimediaWidgets import ...` | `from PySide6.QtMultimediaWidgets import ...` |
| `pyqtSignal` | `Signal` |
| `pyqtSlot` | `Slot` |
| `pyqtProperty` | `Property` |

**影响的非 UI 文件：**
- `main.py`
- `service/task_polling_service.py`
- `service/chat_service.py`
- `storage/orm/base.py`（如有 Qt import）

---

## 实施步骤

### 第一步：依赖切换和 Service 层适配

1. 执行 `uv remove pyqt6 pyqt6-fluent-widgets && uv add PySide6`
2. 全局替换 `service/` 和 `main.py` 中的 `PyQt6` → `PySide6`、`pyqtSignal` → `Signal`
3. 验证：运行测试 `uv run python -m unittest discover tests/`

### 第二步：创建 Bridge 层骨架

1. 创建 `bridge/` 目录和 `__init__.py`
2. 实现 `bridge/app_bridge.py`（AppBridge 空壳 + 信号定义）
3. 实现所有 `bridge/models/` 中的 ListModel 类
4. 迁移 `main_window.py` 中的 Worker 类到 `bridge/workers.py`
5. 更新 `di/containers.py` 注册 AppBridge

### 第三步：创建 QML 骨架

1. 创建 `qml/` 目录结构
2. 实现 `main.qml`（ApplicationWindow + StackView 导航）
3. 实现 `Theme.qml`（颜色/字体常量单例）
4. 实现 `TabBar.qml` + `PageHeader.qml`（基础导航组件）
5. 改造 `main.py` 为 QQmlApplicationEngine 启动
6. 验证：启动应用能看到空壳窗口和 Tab 栏

### 第四步：迁移直接生成模式

1. `Sidebar.qml` + `ConversationListModel`
2. `ChatArea.qml` + `MessageBubble.qml` + `ParameterPanel.qml`
3. `VideoStatusCard.qml` + `SpinnerOverlay.qml`
4. `DirectModePage.qml`（组合以上组件）
5. 实现 `ConversationBridge` + `MessageListModel`
6. 验证：能创建对话、发送消息、看到生成进度

### 第五步：迁移项目管理模式 — 基础页面

1. `ProjectGridPage.qml` + `ProjectCard.qml` + `ProjectListModel`
2. `ProjectDetailPage.qml`（模块入口网格）
3. `ProjectDialog.qml`（创建/编辑）
4. `ProjectChatPage.qml`（三栏布局 + SplitView）
5. 实现 `ProjectBridge`
6. 验证：能创建项目、进入详情、切换模块

### 第六步：迁移编辑器页面

1. `StoryOutlinePage.qml`（TextArea + AI ChatPanel）
2. `ScreenplayPage.qml` + `SceneCard.qml`
3. `StoryboardPage.qml` + `StoryboardCard.qml`（最复杂）
4. `CharacterPage.qml` + `CharacterCard.qml`
5. 实现 `StoryboardBridge` + `CharacterBridge`
6. 验证：各编辑器的 CRUD 操作正常

### 第七步：迁移素材库和播放器

1. `MediaLibraryPage.qml` + `MediaCard.qml`
2. `VideoPlayerPage.qml` + `TimelineWidget.qml`
3. 实现 `MediaBridge` + `VideoPlayerBridge`
4. 验证：视频播放、素材导入/删除正常

### 第八步：迁移对话框和辅助功能

1. `SettingsDialog.qml`
2. `AlertDialog.qml` + `ConfirmDialog.qml`
3. `HistoryDialog.qml`
4. 实现 `SettingsBridge`
5. 验证：设置保存、对话框弹出正常

### 第九步：清理

1. 删除整个 `ui/` 目录
2. 确认 `pyproject.toml` 中无 PyQt6 相关依赖
3. 运行全部测试
4. 打包验证：`uv run pyinstaller ai-video-gui.spec`

---

## 验证方案

每个步骤完成后执行：

1. **单元测试** — `uv run python -m unittest discover tests/`
2. **启动测试** — `uv run main.py` 确认应用能启动
3. **功能验证** — 按每步的"验证"清单逐项检查
4. **打包测试** — 最终步骤执行 PyInstaller 打包确认

---

## 风险与注意事项

### 已知风险

- **PySide6 版本兼容性** — Qt Quick Controls 在 PySide6 6.7+ 中稳定，确保使用足够新的版本
- **QML 性能** — 大量 ListView delegate 实例化时可能有性能问题，需使用 `ListView.clip: true` 和 `cacheBuffer`
- **视频播放** — PySide6 的 `QtMultimedia` 后端实现可能与 PyQt6 不同，需测试 `VideoOutput` + `MediaPlayer` 的兼容性
- **自定义绘制** — `TimelineWidget` 使用大量 QPainter 自定义绘制，QML 中需用 `Canvas` 替代，绘制 API 不同
- **无边框窗口** — 原来用 `qframelesswindow.FramelessDialog`，QML 中 Dialog 组件不需要此库，但如果有全局无边框窗口需求，需用 `QWindow.setFlags(Qt.FramelessWindowHint)`

### 数据兼容性

- **数据库不变** — SQLAlchemy ORM 层、Repository 层、数据模型层完全不依赖 Qt，无需修改
- **配置文件不变** — JSON 配置通过 `ConfigManager` 管理，不依赖 Qt
- **Service 接口不变** — Service 方法签名保持不变，仅 Signal 声明语法变化

### 回滚策略

建议在独立 git 分支上执行迁移：
```bash
git checkout -b feat/qml-migration
```

每个步骤完成后提交一次，方便回滚到任意阶段。
