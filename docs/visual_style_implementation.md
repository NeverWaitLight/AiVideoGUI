# 视频风格系统实现文档

## 概述

视频风格系统允许用户为项目选择不同的视觉风格，这些风格将应用于角色设计图、分镜设计图和最终视频生成。

## 数据库设计

### 表结构：`visual_styles`

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| name | VARCHAR(100) | 风格名称，唯一 |
| is_default | BOOLEAN | 是否为默认风格 |
| sample_image_path | VARCHAR(500) | 示例图片路径 |
| created_at | INTEGER | 创建时间（毫秒时间戳） |
| updated_at | INTEGER | 更新时间（毫秒时间戳） |

### 索引

- `idx_visual_styles_created_at` - 按创建时间降序
- `idx_visual_styles_name` - 按名称

## 代码架构

### 1. 数据模型 (`models/visual_style.py`)

```python
@dataclass
class VisualStyle:
    id: int
    name: str
    is_default: bool
    sample_image_path: str
    created_at: int
    updated_at: int
```

### 2. ORM 实体 (`storage/orm/visual_style_entity.py`)

使用 SQLAlchemy 2.0 映射到 `visual_styles` 表。

### 3. Repository (`storage/repositories/visual_style_repository.py`)

**核心方法：**
- `list_all()` - 获取所有风格
- `get_by_id(style_id)` - 根据 ID 获取
- `get_default_style()` - 获取默认风格
- `exists_by_name(name)` - 检查名称是否存在
- `clear_all_defaults()` - 清除所有默认标记
- `save(style)` - 保存风格
- `delete(style_id)` - 删除风格
- `update_style(...)` - 更新风格

### 4. Service (`service/visual_style_service.py`)

**业务逻辑：**
- 创建风格时检查名称唯一性
- 设置默认风格时自动清除其他默认标记
- 完整的事务管理和错误处理

**核心方法：**
- `create_style(name, is_default, sample_image_path)`
- `list_styles()`
- `get_style(style_id)`
- `get_default_style()`
- `update_style(style_id, name, is_default, sample_image_path)`
- `delete_style(style_id)`

### 5. 依赖注入 (`di/containers.py`)

```python
visual_style_service = providers.Singleton(
    VisualStyleService,
    session_manager=session_manager,
)
```

### 6. 数据库迁移 (`alembic/versions/e9c8cffe2ba1_add_visual_styles_table.py`)

使用 Alembic 管理数据库变更，应用启动时自动升级到最新版本。

**迁移内容：**
- 创建 `visual_styles` 表（包含索引）
- 插入 14 条预设风格数据
- 支持 upgrade 和 downgrade

**应用启动流程（`main.py`）：**
```python
# 初始化数据库引擎
init_engine(database_url, echo=False)

# 使用 Alembic 进行数据库迁移
from alembic.config import Config
from alembic import command
alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
alembic_cfg.set_main_option("sqlalchemy.url", database_url)
command.upgrade(alembic_cfg, "head")
```

**优点：**
- ✅ 版本控制：每次变更都有记录，可追溯
- ✅ 可回滚：支持 downgrade 操作
- ✅ 自动化：应用启动时自动升级
- ✅ 符合最佳实践：业界标准的迁移工具

**预设风格列表（14 种）：**
1. 毛毡风格 ✓ (默认)
2. 3D卡通
3. 像素风格
4. 木偶动画
5. 黏土风格
6. 黑白动画
7. 水彩插画
8. 日本动画
9. 赛博朋克
10. 剪纸风格
11. 油画风格
12. 低多边形
13. 电影风格
14. 写实风格

## 使用方式

### 在应用中获取 Service

```python
# 通过 DI 容器
container = ApplicationContainer()
visual_style_service = container.visual_style_service()

# 获取所有风格
styles = visual_style_service.list_styles()

# 获取默认风格
default_style = visual_style_service.get_default_style()
```

### 创建新风格

```python
new_style = visual_style_service.create_style(
    name="复古动画",
    is_default=False,
    sample_image_path="resources/styles/retro.png"
)
```

### 更新风格（切换默认）

```python
success = visual_style_service.update_style(
    style_id=2,
    name="3D卡通",
    is_default=True,  # 设为默认，会自动清除其他默认标记
    sample_image_path="resources/styles/3d_cartoon.png"
)
```

## Alembic 使用指南

### 生成新的迁移

```bash
# 自动检测 ORM 变更
uv run alembic revision --autogenerate -m "description"

# 手动创建空迁移
uv run alembic revision -m "description"
```

### 应用迁移

```bash
# 升级到最新版本
uv run alembic upgrade head

# 升级一个版本
uv run alembic upgrade +1

# 升级到指定版本
uv run alembic upgrade <revision_id>
```

### 回滚迁移

```bash
# 回滚一个版本
uv run alembic downgrade -1

# 回滚到指定版本
uv run alembic downgrade <revision_id>

# 回滚所有迁移
uv run alembic downgrade base
```

### 查看迁移状态

```bash
# 查看当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history

# 查看详细信息
uv run alembic history --verbose
```

## 测试验证

所有功能均已通过测试：

- ✅ Alembic 迁移执行成功
- ✅ 表结构创建正确
- ✅ 14 条预设数据插入成功
- ✅ 默认风格设置正确
- ✅ CRUD 操作正常
- ✅ 迁移回滚功能正常

## 后续任务

根据 `video_style_design.md`，还需完成：

1. 新增对应的列表页面和详情页面（QML UI）
2. 项目新增/编辑时增加风格选择
3. ✅ **角色设计图提示词模板增加画面风格**（已完成）
4. ✅ **分镜设计图提示词模板增加画面风格**（已完成）
5. 分镜视频提示词模板增加画面风格

## 已完成功能详解

### 角色设计图视觉风格集成（已完成）

**实现路径：**
1. `prompts/templates/character_image_prompt.yaml` - 添加 `{visual_style}` 和 `{visual_style_instruction}` 占位符
2. `prompts/text_prompt_builder.py` - `build_character_design_image_prompt_messages()` 添加 `visual_style` 参数
3. `service/text_model_service.py` - `generate_character_design_image_prompt()` 添加 `visual_style` 参数
4. `bridge/workers.py` - `CharacterDesignImageWorker` 添加 `visual_style` 参数
5. `bridge/character_bridge.py` - `generate_design_image()` 自动从项目获取视觉风格，未设置时使用默认风格

**逻辑流程：**
- 从项目获取 `visual_style_id`
- 如果未设置，通过 `visual_style_service.get_default_style()` 获取默认风格
- 将风格名称传递到提示词构建器
- 生成的提示词包含风格指导，例如："整体画面采用【毛毡风格】风格，在保持角色三视图规范的前提下，画面色调、光影、质感应符合该风格特点"

### 分镜设计图视觉风格集成（已完成）

**实现路径：**
1. `prompts/templates/image_prompt.yaml` - 添加 `{visual_style}` 和 `{visual_style_instruction}` 占位符
2. `prompts/text_prompt_builder.py` - `build_design_image_prompt_messages()` 添加 `visual_style` 参数和风格指导文本生成
3. `service/text_model_service.py` - `generate_design_image_prompt()` 添加 `visual_style` 参数，日志记录风格信息
4. `bridge/workers.py` - `DesignImageWorker` 和 `BatchDesignImageWorker` 添加 `visual_style` 参数
5. `bridge/storyboard_bridge.py` - `generate_design_image()` 和 `batch_generate_design_images()` 自动从项目获取视觉风格
6. `bridge/app_bridge.py` - 确保 `StoryboardBridge` 注入了 `visual_style_service`

**逻辑流程：**
- 单个/批量生成分镜设计图时，从项目获取 `visual_style_id`
- 如果未设置，通过 `visual_style_service.get_default_style()` 获取默认风格
- 将风格名称传递到提示词构建器
- 生成的提示词包含风格指导，例如："整体画面采用【3D卡通】风格，在保持黑白素描分镜稿规范的前提下，画面构图、光影、线条质感应符合该风格特点"
- 日志记录使用的视觉风格，便于调试

**关键设计点：**
- 分镜设计图保持黑白素描底色，但构图和光影质感会受视觉风格影响
- 风格指导文本通过 `visual_style_instruction` 占位符注入到 system_prompt
- 风格名称通过 `visual_style` 占位符注入到 user_prompt
- 未设置风格时自动使用默认风格，确保一致的用户体验
