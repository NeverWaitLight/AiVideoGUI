视频生成时支持传递参考图片（分镜设计图 + 角色设计图），并在 Prompt 中添加【参考图片说明】部分，告诉 AI 模型每张图片的用途。

## Prompt 结构

在视频生成 Prompt 中新增【参考图片说明】部分，位于【场景上下文】之后、【镜头画面】之前：

```
【场景上下文】
第 1 场 · 内景 · 胖橘猫的厨房 · 日

【参考图片说明】
图1：本镜头的分镜设计图，请参考其构图、机位、光线、色调和整体氛围。
图2：胖橘猫的角色设计图，请严格参考其外观、服装、神态等视觉特征。

【镜头画面】
胖橘猫穿着特制的小围裙站在厨房里...

【镜头参数】
景别：中景 | 运镜：固定 | 时长：5.0秒
```

## 技术实现

### VideoPromptBuilder

`build_shot_prompt()` 新增 `reference_images` 参数，接收参考图片信息列表。新增辅助方法 `_build_reference_images_desc()` 构建说明文本：

- **design 类型**：提示参考构图、机位、光线、色调
- **character 类型**：提示参考外观、服装、神态，并包含角色名称

### StoryboardBridge

`batch_generate_videos()` 中维护两个列表：

- `reference_images_paths` — 文件绝对路径列表，用于 API 上传
- `reference_images_info` — 类型和元数据列表，用于生成 Prompt 说明

**图片顺序约定**
- 图1 = 分镜设计图（如果有）
- 图2-N = 角色设计图（按匹配顺序）

**角色设计图匹配逻辑**
- 遍历所有角色，检查角色名称或代号是否出现在 `visual_content` 中
- 最多添加 5 张参考图片

## 向后兼容

- `reference_images` 参数默认为 `None`
- 旧代码不传递该参数时，不会生成【参考图片说明】部分

## 涉及文件

- `prompts/video_prompt_builder.py` — 新增参考图片说明构建
- `bridge/storyboard_bridge.py` — 传递参考图片信息
