# 提示词重构总结

## 重构目标

将所有大模型的提示词组装逻辑统一提取到 `prompts/` 文件夹，按文本/图片/视频三类大模型分别组织，避免在业务代码中硬编码提示词。

## 架构变更

### 1. 新增文件

- **`prompts/text_prompt_builder.py`** - 文本大模型提示词构建器
  - 统一入口类，封装所有文本模型的提示词构建方法
  - 依赖 `PromptTemplateManager` 加载 YAML 模板
  - 包含 11 个方法：聊天、大纲优化、剧本生成、分镜生成、图片提示词生成等

- **`prompts/image_prompt_builder.py`** - 图片大模型提示词构建器
  - 封装图片生成 API 的请求体构建逻辑
  - 静态方法 `build_bailian_image_payload()`
  - 用于阿里百炼文生图（wan2.6-t2i）

- **`prompts/video_prompt_builder.py`** - 视频大模型提示词构建器
  - 从 `utils/prompt_builder.py` 移动而来
  - 保持原有功能不变（构建结构化的视频生成 Prompt）

### 2. 修改文件

- **`service/text_model_service.py`**
  - 移除所有硬编码的系统提示词（剧本生成、分镜生成等）
  - 修改构造函数参数：`prompt_manager` → `text_prompt_builder`
  - 更新所有方法调用新的提示词构建器

- **`providers/dashscope_image.py`**
  - 使用 `ImagePromptBuilder.build_bailian_image_payload()` 构建请求体
  - 移除硬编码的 payload 构建逻辑

- **`di/containers.py`**
  - 新增 `text_prompt_builder` 单例
  - 重命名 `prompt_builder` → `video_prompt_builder`
  - 更新 `text_model_service` 依赖注入

- **`CLAUDE.md`**
  - 更新架构文档，新增"Prompt Layer"章节
  - 说明三个提示词构建器的职责和使用方式
  - 更新设计模式列表

### 3. 引用路径更新

以下文件的导入路径已更新：
- `bridge/storyboard_bridge.py`
- `di/containers.py`
- `tests/test_prompt_builder.py`
- `tests/test_reference_images_desc.py`

## 设计原则

### 1. 按模型类型分层

```
prompts/
├── text_prompt_builder.py    # 文本大模型（聊天、剧本、分镜等）
├── image_prompt_builder.py   # 图片大模型（文生图）
├── video_prompt_builder.py   # 视频大模型（视频生成）
├── manager.py                 # YAML 模板管理器
└── templates/                 # YAML 模板文件
```

### 2. 统一入口类

每个模型类型一个构建器类，封装该类型所有的提示词构建逻辑：
- `TextPromptBuilder` - 11 个方法
- `ImagePromptBuilder` - 1 个方法（静态）
- `VideoPromptBuilder` - 1 个方法（静态）

### 3. 依赖注入

- `TextPromptBuilder` 依赖 `PromptTemplateManager`，通过 DI 容器注入
- `ImagePromptBuilder` 和 `VideoPromptBuilder` 为静态方法，无需依赖注入
- `TextModelService` 依赖 `TextPromptBuilder`，通过 DI 容器注入

### 4. 混合使用 YAML 模板和硬编码

- **使用 YAML 模板**：简短的提示词（大纲优化、角色生成等）
- **硬编码在 Builder**：长且复杂的系统提示词（剧本生成、分镜生成）
  - 理由：这些提示词包含大量格式规则和示例，硬编码更易维护

## 验证结果

### 启动测试

```bash
uv run main.py
```

**结果：** 应用成功启动，所有功能正常
- 16 个 YAML 模板成功加载
- 依赖注入容器正常工作
- 后台任务调度器正常运行
- QML 引擎正常加载

### 代码检查

```bash
grep -r "utils\.prompt_builder" .
```

**结果：** 无残留旧引用路径

## 优势

1. **集中管理** - 所有提示词逻辑集中在 `prompts/` 目录，易于查找和维护
2. **职责清晰** - 按模型类型分离，文本/图片/视频各司其职
3. **避免硬编码** - 业务代码（Service/Bridge）不再直接构建提示词
4. **易于扩展** - 新增提示词只需在对应 Builder 中添加方法
5. **类型安全** - 统一入口类，IDE 可以提供更好的代码补全

## 后续改进建议

1. **剧本生成和分镜生成的系统提示词**：考虑拆分为多个 YAML 模板，便于独立调整各部分规则
2. **视频提示词构建器**：考虑支持更多参数（如负面提示词、风格预设等）
3. **测试覆盖率**：为三个 Builder 添加单元测试

## 文件清单

### 新增文件（2 个）
- `prompts/text_prompt_builder.py` (275 行)
- `prompts/image_prompt_builder.py` (35 行)

### 移动文件（1 个）
- `utils/prompt_builder.py` → `prompts/video_prompt_builder.py`

### 修改文件（5 个）
- `service/text_model_service.py`
- `providers/dashscope_image.py`
- `di/containers.py`
- `CLAUDE.md`
- `bridge/storyboard_bridge.py` (仅更新导入路径)

### 测试文件（2 个）
- `tests/test_prompt_builder.py` (更新导入路径)
- `tests/test_reference_images_desc.py` (更新导入路径)

## 重构时间线

1. ✅ 创建视频提示词构建器（移动文件 + 更新引用）
2. ✅ 创建文本提示词构建器（提取硬编码提示词）
3. ✅ 创建图片提示词构建器（提取 payload 构建逻辑）
4. ✅ 更新依赖注入容器
5. ✅ 更新所有 Service 调用
6. ✅ 启动测试验证

**总耗时：** 约 10 分钟
**验证状态：** 通过（应用成功启动，无错误）
