提示词系统经历了两个阶段的重构：首先将散落在业务代码中的提示词集中到 `prompts/` 目录，然后将硬编码的提示词全部提取到 YAML 模板文件。

## 架构

```
prompts/
├── text_prompt_builder.py    # 文本大模型（聊天、剧本、分镜等）— 11 个方法
├── image_prompt_builder.py   # 图片大模型（文生图）— 1 个静态方法
├── video_prompt_builder.py   # 视频大模型（视频生成）— 1 个静态方法
├── manager.py                # YAML 模板管理器
└── templates/                # YAML 模板文件（19 个）
```

**按模型类型分层**
- **TextPromptBuilder** — 封装所有文本模型的提示词构建（11 个方法），依赖 `PromptTemplateManager` 加载 YAML 模板
- **ImagePromptBuilder** — 封装图片生成 API 的请求体构建（静态方法）
- **VideoPromptBuilder** — 构建结构化的视频生成 Prompt（静态方法，从 `utils/prompt_builder.py` 移动而来）

## 依赖注入

- `TextPromptBuilder` 依赖 `PromptTemplateManager`，通过 DI 容器注入
- `ImagePromptBuilder` 和 `VideoPromptBuilder` 为静态方法，无需依赖注入
- `ChatModelService` 依赖 `TextPromptBuilder`，通过 DI 容器注入

## YAML 模板覆盖率

TextPromptBuilder 的 11 个方法全部使用 YAML 模板（100% 覆盖率）：

| 方法 | 模板文件 |
|:---|:---|
| `build_chat_messages()` | `chat.yaml` |
| `build_outline_optimization_messages()` | `outline_optimization.yaml` |
| `build_script_generation_messages()` | `script_generation.yaml` |
| `build_storyboard_generation_messages()` | `storyboard_generation_with_characters.yaml` |
| `build_design_image_prompt_messages()` | `image_prompt_generation.yaml` |
| `build_character_design_image_prompt_messages()` | `character_image_prompt_generation.yaml` |
| `build_screenplay_optimization_messages()` | `screenplay_optimization.yaml` |
| `build_character_generation_messages()` | `character_generation.yaml` |
| `build_character_optimization_messages()` | `character_optimization.yaml` |
| `build_storyboard_optimization_messages()` | `storyboard_optimization.yaml` |
| `build_character_description_refine_messages()` | `character_description_refine.yaml` |

## 重构前后对比

**重构前：** 业务代码中硬编码 50+ 行的系统提示词

**重构后：** 业务代码仅 5 行调用，提示词内容全部在 YAML 文件中

## 优势

- **集中管理** — 所有提示词集中在 `prompts/templates/` 目录
- **职责清晰** — Python 代码专注业务逻辑，YAML 文件专注提示词内容
- **易于修改** — 调整提示词无需修改 Python 代码
- **版本控制友好** — YAML 文件的 diff 更清晰
- **易于扩展** — 新增提示词只需在对应 Builder 中添加方法

## 涉及文件

**新增文件**
- `prompts/text_prompt_builder.py` (275 行)
- `prompts/image_prompt_builder.py` (35 行)
- `prompts/templates/script_generation.yaml`
- `prompts/templates/storyboard_generation_with_characters.yaml`
- `prompts/templates/character_description_refine.yaml`

**移动文件**
- `utils/prompt_builder.py` → `prompts/video_prompt_builder.py`

**修改文件**
- `service/text_model_service.py` — 移除所有硬编码提示词，改用 TextPromptBuilder
- `providers/dashscope_image.py` — 使用 ImagePromptBuilder
- `di/containers.py` — 新增 text_prompt_builder 单例
- `bridge/storyboard_bridge.py` — 更新导入路径
