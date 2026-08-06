视频风格系统允许用户为项目选择不同的视觉风格，这些风格将应用于角色设计图、分镜设计图和最终视频生成。

## 数据库设计

`visual_styles` 表结构：

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | INTEGER | 主键，自增 |
| name | VARCHAR(100) | 风格名称，唯一 |
| is_default | BOOLEAN | 是否为默认风格 |
| sample_image_path | VARCHAR(500) | 示例图片路径 |
| created_at | INTEGER | 创建时间（毫秒时间戳） |
| updated_at | INTEGER | 更新时间（毫秒时间戳） |

## 预设风格（14 种）

毛毡风格（默认）、3D卡通、像素风格、木偶动画、黏土风格、黑白动画、水彩插画、日本动画、赛博朋克、剪纸风格、油画风格、低多边形、电影风格、写实风格

## 代码架构

- **数据模型** — `models/visual_style.py`
- **ORM 实体** — `storage/orm/visual_style_entity.py`
- **Repository** — `storage/repositories/visual_style_repository.py`
- **Service** — `service/visual_style_service.py`（创建时检查名称唯一性，设置默认时自动清除其他默认标记）
- **依赖注入** — `di/containers.py` 注册为 Singleton
- **数据库迁移** — `alembic/versions/e9c8cffe2ba1_add_visual_styles_table.py`

## 设计图集成

### 角色设计图

**逻辑流程：**
1. 从项目获取 `visual_style_id`
2. 如果未设置，通过 `visual_style_service.get_default_style()` 获取默认风格
3. 将风格名称传递到提示词构建器
4. 生成的提示词包含风格指导，例如："整体画面采用【毛毡风格】风格，在保持角色三视图规范的前提下，画面色调、光影、质感应符合该风格特点"

**涉及文件：**
- `prompts/templates/character_image_prompt.yaml` — 添加 `{visual_style}` 和 `{visual_style_instruction}` 占位符
- `prompts/text_prompt_builder.py` — `build_character_design_image_prompt_messages()` 添加 `visual_style` 参数
- `service/text_model_service.py` — `generate_character_design_image_prompt()` 添加 `visual_style` 参数
- `bridge/workers.py` — `CharacterDesignImageWorker` 添加 `visual_style` 参数
- `bridge/character_bridge.py` — `generate_design_image()` 自动获取视觉风格

### 分镜设计图

**逻辑流程：**
1. 单个/批量生成分镜设计图时，从项目获取 `visual_style_id`
2. 如果未设置，通过 `visual_style_service.get_default_style()` 获取默认风格
3. 将风格名称传递到提示词构建器
4. 生成的提示词包含风格指导，例如："整体画面采用【3D卡通】风格，在保持黑白素描分镜稿规范的前提下，画面构图、光影、线条质感应符合该风格特点"

**涉及文件：**
- `prompts/templates/image_prompt.yaml` — 添加占位符
- `prompts/text_prompt_builder.py` — `build_design_image_prompt_messages()` 添加 `visual_style` 参数和风格指导文本
- `service/text_model_service.py` — `generate_design_image_prompt()` 添加 `visual_style` 参数
- `bridge/workers.py` — `DesignImageWorker` 和 `BatchDesignImageWorker` 添加 `visual_style` 参数
- `bridge/storyboard_bridge.py` — `generate_design_image()` 和 `batch_generate_design_images()` 自动获取视觉风格

### 两者差异

| 对比项 | 角色设计图 | 分镜设计图 |
|:---|:---|:---|
| 模板文件 | `character_image_prompt.yaml` | `image_prompt.yaml` |
| 风格应用方式 | 彩色三视图，直接应用风格 | 黑白素描，风格影响构图和光影 |
| 默认风格文案 | "通用电影概念设计风格" | "黑白素描风格" |

## 向后兼容

- 所有新增参数均为可选参数（`visual_style: str = ""`）
- 不影响现有代码调用
- 旧项目数据无 `visual_style_id` 时自动回退到默认风格

## 待完成功能

- 新增对应的列表页面和详情页面（QML UI）
- 项目新增/编辑时增加风格选择
- 分镜视频提示词模板增加画面风格
