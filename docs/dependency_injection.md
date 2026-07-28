# 依赖注入（DI）使用指南

本项目使用 [dependency-injector](https://python-dependency-injector.ets-labs.org/) 框架管理所有 Service 和基础设施的依赖关系。

## 核心概念

### 1. 依赖注入容器（ApplicationContainer）

位于 `di/containers.py`，管理所有对象的创建和生命周期：

```python
from di import ApplicationContainer

# 创建容器实例
container = ApplicationContainer()

# 配置容器（必需）
container.config.workspace_root.from_value("/path/to/workspace")
container.config.config_path.from_value("/path/to/config.json")

# 获取 Service 实例（自动注入依赖）
video_service = container.video_service()
project_service = container.project_service()
```

### 2. 单例模式（Singleton）

所有 Service 和基础设施使用单例模式：

```python
# 多次调用返回同一实例
service1 = container.video_service()
service2 = container.video_service()
assert service1 is service2  # True
```

### 3. 自动依赖注入

容器会自动解析并注入依赖：

```python
# VideoService 需要 SessionManager 和 ConfigManager
# 容器会自动创建这些依赖并注入
video_service = container.video_service()

# 等价于手动注入：
# session_manager = SessionManager()
# config_manager = ConfigManager(config_path)
# video_service = VideoService(session_manager, config_manager)
```

## 当前架构

### 基础设施层

```python
container.session_manager()     # SessionManager（数据库会话管理）
container.config_manager()      # ConfigManager（配置文件管理）
container.prompt_builder()      # VideoPromptBuilder（Prompt 构建工具）
```

### Service 层

```python
container.video_service()           # 视频生成服务
container.media_service()           # 素材库服务
container.project_service()         # 项目管理服务
container.story_outline_service()   # 故事大纲服务
container.screenplay_service()      # 剧本服务
container.storyboard_service()      # 分镜服务
container.character_service()       # 角色管理服务
container.chat_service()            # 对话服务
container.text_model_service()      # 文本模型服务
container.image_service()           # 图片生成服务
container.task_polling_service()    # 任务轮询服务
```

## 使用场景

### 1. 主窗口初始化（MainWindow）

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建并配置容器
        self._container = ApplicationContainer()
        self._container.config.workspace_root.from_value(root)
        self._container.config.config_path.from_value(config_path)
        
        # 获取所有需要的 Service
        self._service = self._container.video_service()
        self._project_service = self._container.project_service()
        self._media_service = self._container.media_service()
        # ... 其他 Service
```

### 2. 传递容器给子组件

```python
class _BatchGenerationController(QObject):
    def __init__(
        self,
        shot_list: list[dict],
        container: ApplicationContainer,  # 传递容器而非单个 Service
        provider_name: str,
        model_name: str,
        project,
        provider_cfg,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._container = container
        
        # 从容器获取需要的 Service
        self._service = container.video_service()
        self._polling = container.task_polling_service()
```

### 3. 测试中使用（Mock 依赖）

```python
import unittest
from di import ApplicationContainer

class TestVideoService(unittest.TestCase):
    def setUp(self):
        # 创建测试容器
        self.container = ApplicationContainer()
        self.container.config.workspace_root.from_value("/tmp/test")
        self.container.config.config_path.from_value("/tmp/test/config.json")
        
        # 可以覆盖单个依赖为 Mock
        from unittest.mock import Mock
        mock_session = Mock()
        self.container.session_manager.override(providers.Object(mock_session))
        
        # 获取被测试的 Service（自动注入 Mock 依赖）
        self.service = self.container.video_service()
    
    def tearDown(self):
        self.container.reset_singletons()
```

## 添加新 Service

### 1. 在容器中注册

编辑 `di/containers.py`：

```python
from service.new_service import NewService

class ApplicationContainer(containers.DeclarativeContainer):
    # ... 现有配置 ...
    
    # 新增 Service（单例，自动注入依赖）
    new_service = providers.Singleton(
        NewService,
        session_manager=session_manager,      # 注入 SessionManager
        config=config_manager,                # 注入 ConfigManager
        other_param=config.some_config_value, # 注入配置值
    )
```

### 2. 参数名匹配

确保容器中的参数名与 Service 构造函数参数名一致：

```python
# Service 构造函数
class NewService:
    def __init__(self, session_manager: SessionManager, config: ConfigManager):
        self._sm = session_manager
        self._config = config

# 容器配置（参数名必须匹配）
new_service = providers.Singleton(
    NewService,
    session_manager=session_manager,  # ✅ 正确
    config=config_manager,            # ✅ 正确
)

# ❌ 错误示例（参数名不匹配）
new_service = providers.Singleton(
    NewService,
    session_mgr=session_manager,      # ❌ 应该是 session_manager
    config_manager=config_manager,    # ❌ 应该是 config
)
```

### 3. 在主窗口中使用

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # ... 容器初始化 ...
        
        # 获取新 Service
        self._new_service = self._container.new_service()
```

## 常见参数名约定

根据项目现有代码的参数命名：

| Service | SessionManager 参数名 | ConfigManager 参数名 |
|---------|----------------------|---------------------|
| VideoService | `session_manager` | `config` |
| ChatService | - | `config` |
| TextModelService | - | `config_manager` |
| ImageService | - | `config_manager` |
| MediaService | `session_manager` | - |
| ProjectService | `session_manager` | - |
| StoryboardService | `session_mgr` | - |
| TaskPollingService | `session_manager` | `config` |

**注意：** 不同 Service 的参数名可能不一致（历史遗留），添加新 Service 时需要检查构造函数签名。

## 优势对比

### 重构前（手动依赖注入）

```python
# MainWindow.__init__() 中手动创建所有依赖（50+ 行）
self._session_manager = SessionManager()
self._config = ConfigManager(config_path)
self._service = VideoService(self._session_manager, self._config)
self._chat_service = ChatService(self._config)
self._project_service = ProjectService(self._session_manager, root)
self._story_outline_service = StoryOutlineService(self._session_manager)
self._screenplay_service = ScreenplayService(self._session_manager)
self._storyboard_service = StoryboardService(self._session_manager)
self._character_service = CharacterService(self._session_manager)
self._text_model_service = TextModelService(self._config)
self._image_service = ImageService(self._config)
self._media_service = MediaService(self._session_manager, root)
self._polling_service = TaskPollingService(
    session_manager=self._session_manager,
    config=self._config,
    workspace_root=root,
    provider_registry=_PROVIDER_REGISTRY,
)
self._polling_service.set_media_service(self._media_service)
```

### 重构后（DI 容器）

```python
# MainWindow.__init__() 中使用容器（简洁清晰）
self._container = ApplicationContainer()
self._container.config.workspace_root.from_value(root)
self._container.config.config_path.from_value(config_path)

# 获取 Service 实例（自动注入依赖）
self._service = self._container.video_service()
self._project_service = self._container.project_service()
self._media_service = self._container.media_service()
# ... 其他 Service
```

### 主要改进

1. **集中管理**：所有依赖关系定义在 `di/containers.py` 一处
2. **类型安全**：依赖关系在容器定义时静态检查
3. **易于测试**：可以轻松覆盖单个依赖为 Mock 对象
4. **生命周期管理**：单例模式自动管理，避免重复创建
5. **可读性提升**：主窗口初始化代码从 50+ 行减少到 10+ 行

## 参考资料

- [dependency-injector 官方文档](https://python-dependency-injector.ets-labs.org/)
- [Python 依赖注入最佳实践](https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html)
