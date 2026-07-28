# 依赖注入（DI）框架集成总结

## 变更概述

成功引入 `dependency-injector` 框架，替代手动依赖注入，实现了集中式依赖管理。

## 核心变更

### 1. 新增文件

- **`di/containers.py`** - 依赖注入容器定义
  - 管理所有 Service 和基础设施的生命周期
  - 使用单例模式确保全局唯一实例
  - 自动解析并注入依赖关系

- **`di/__init__.py`** - 模块导出
  - 对外暴露 `ApplicationContainer`

- **`docs/dependency_injection.md`** - 完整使用文档
  - 核心概念说明
  - 使用场景示例
  - 添加新 Service 的步骤
  - 优势对比分析

- **`tests/test_dependency_injection.py`** - 单元测试
  - 验证单例模式
  - 验证依赖注入
  - 验证配置传播
  - 验证所有 Service 可实例化
  - 验证共享 SessionManager

### 2. 修改文件

- **`ui/main_window.py`**
  - 使用 `ApplicationContainer` 替代手动创建 Service
  - 从 50+ 行初始化代码简化为 10+ 行
  - `_BatchGenerationController` 接收容器而非单个 Service

- **`CLAUDE.md`**
  - 更新技术栈，添加 `dependency-injector`
  - 新增 "Dependency Injection" 架构层说明
  - 更新依赖关系图
  - 在 "Key Design Patterns" 中添加 DI 容器模式

### 3. 依赖包

- **新增：** `dependency-injector==4.49.1`
  - 通过 `uv add dependency-injector` 安装
  - 自动更新 `pyproject.toml` 和 `uv.lock`

## 架构改进

### 重构前（手动依赖注入）

```python
# MainWindow.__init__() - 手动创建所有依赖（50+ 行）
self._session_manager = SessionManager()
self._config = ConfigManager(os.path.join(data_dir, "config.json"))
self._service = VideoService(self._session_manager, self._config)
self._chat_service = ChatService(self._config)
self._project_service = ProjectService(self._session_manager, self._root)
self._story_outline_service = StoryOutlineService(self._session_manager)
# ... 10+ 个 Service
self._polling_service = TaskPollingService(
    session_manager=self._session_manager,
    config=self._config,
    workspace_root=self._root,
    provider_registry=_PROVIDER_REGISTRY,
)
self._polling_service.set_media_service(self._media_service)
```

### 重构后（DI 容器）

```python
# MainWindow.__init__() - 使用容器（10+ 行）
self._container = ApplicationContainer()
self._container.config.workspace_root.from_value(root)
self._container.config.config_path.from_value(os.path.join(data_dir, "config.json"))

# 获取 Service 实例（自动注入依赖）
self._service = self._container.video_service()
self._project_service = self._container.project_service()
self._media_service = self._container.media_service()
# ... 其他 Service
```

## 主要优势

### 1. 集中管理
- 所有依赖关系定义在 `di/containers.py` 一处
- 修改依赖关系无需改动多个文件
- 依赖图清晰可见

### 2. 类型安全
- 依赖关系在容器定义时静态检查
- IDE 自动补全和类型提示支持
- 编译时发现依赖错误

### 3. 易于测试
- 可以轻松覆盖单个依赖为 Mock 对象
- 测试隔离性更好
- 支持依赖注入测试模式

### 4. 生命周期管理
- 单例模式自动管理，避免重复创建
- 容器管理对象生命周期
- 支持 `reset_singletons()` 重置状态

### 5. 可读性提升
- 主窗口初始化代码从 50+ 行减少到 10+ 行
- 依赖关系更清晰
- 代码维护成本降低

## 容器配置结构

```python
ApplicationContainer
├── config (Configuration)
│   ├── workspace_root: str
│   └── config_path: str
├── 基础设施层
│   ├── session_manager: SessionManager (Singleton)
│   ├── config_manager: ConfigManager (Singleton)
│   └── prompt_builder: VideoPromptBuilder (Singleton)
└── Service 层
    ├── video_service: VideoService (Singleton)
    ├── media_service: MediaService (Singleton)
    ├── project_service: ProjectService (Singleton)
    ├── story_outline_service: StoryOutlineService (Singleton)
    ├── screenplay_service: ScreenplayService (Singleton)
    ├── storyboard_service: StoryboardService (Singleton)
    ├── character_service: CharacterService (Singleton)
    ├── chat_service: ChatService (Singleton)
    ├── text_model_service: TextModelService (Singleton)
    ├── image_service: ImageService (Singleton)
    └── task_polling_service: TaskPollingService (Singleton)
```

## 注意事项

### 参数名匹配

容器中的参数名必须与 Service 构造函数参数名一致：

```python
# ✅ 正确（参数名匹配）
class VideoService:
    def __init__(self, session_manager: SessionManager, config: ConfigManager):
        ...

video_service = providers.Singleton(
    VideoService,
    session_manager=session_manager,  # ✅
    config=config_manager,            # ✅
)

# ❌ 错误（参数名不匹配）
video_service = providers.Singleton(
    VideoService,
    session_mgr=session_manager,      # ❌ 应该是 session_manager
    config_manager=config_manager,    # ❌ 应该是 config
)
```

### 现有代码的参数名不一致

由于历史遗留，不同 Service 的参数名可能不一致：

| Service | SessionManager 参数名 | ConfigManager 参数名 |
|---------|----------------------|---------------------|
| VideoService | `session_manager` | `config` |
| ChatService | - | `config` |
| TextModelService | - | `config_manager` |
| ImageService | - | `config_manager` |
| StoryboardService | `session_mgr` | - |

添加新 Service 时需要检查构造函数签名。

## 测试结果

所有测试通过：

```bash
$ uv run python -m unittest tests.test_dependency_injection -v
test_all_services_instantiation ... ok
test_config_propagation ... ok
test_dependency_injection ... ok
test_shared_session_manager ... ok
test_singleton_pattern ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.011s

OK
```

## 应用启动验证

应用成功启动，日志输出正常：

```
[INFO] 应用启动
[INFO] 数据库引擎初始化完成
[INFO] 数据库表已创建
[DEBUG] SessionManager 初始化完成
[INFO] 配置已加载，providers=[]
[DEBUG] 创建并缓存 Repository 实例
[INFO] 轮询服务已启动
[INFO] 轮询线程进入主循环
```

## 后续改进建议

1. **统一参数命名**
   - 逐步将所有 Service 的 SessionManager 参数统一为 `session_manager`
   - 将所有 ConfigManager 参数统一为 `config_manager`

2. **扩展容器功能**
   - 添加 Repository 层到容器（当前 Repository 通过 SessionManager 获取）
   - 支持作用域（Scoped）依赖（当前仅支持单例）

3. **增强测试覆盖**
   - 添加更多集成测试
   - 测试依赖循环检测
   - 测试容器重置功能

4. **文档完善**
   - 添加 UML 类图展示依赖关系
   - 补充更多实际使用案例
   - 编写故障排查指南

## 参考资料

- [dependency-injector 官方文档](https://python-dependency-injector.ets-labs.org/)
- [项目内部文档](docs/dependency_injection.md)
- [单元测试](tests/test_dependency_injection.py)
