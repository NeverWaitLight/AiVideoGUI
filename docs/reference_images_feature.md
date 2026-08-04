# 参考图片说明功能示例

## 修改前的 Prompt（没有参考图片说明）

```
【场景上下文】
第 1 场 · 内景 · 胖橘猫的厨房 · 日
胖橘猫穿着特制的小围裙站在厨房里，面前摆放着一只透明玻璃杯和一瓶干净的饮用水。他显得既兴奋又有些紧张。

【镜头画面】
胖橘猫穿着特制的小围裙站在厨房里，面前摆放着一只透明玻璃杯和一瓶干净的饮用水。他显得既兴奋又有些紧张。

【镜头参数】
景别：中景 | 运镜：固定 | 时长：5.0秒

【台词】
"今天我们要学习的是如何正确地喝水。首先，选择一个合适的杯子非常重要。"

【连贯性提示】
后一镜：胖橘猫开始演示如何平稳地将水倒入杯子内...

【备注】
暖黄调，自然光线从窗户透入
```

**问题：** API 请求中传递了两张参考图片（分镜设计图 + 角色设计图），但 prompt 中没有说明这些图片的用途。

---

## 修改后的 Prompt（包含参考图片说明）

```
【场景上下文】
第 1 场 · 内景 · 胖橘猫的厨房 · 日
胖橘猫穿着特制的小围裙站在厨房里，面前摆放着一只透明玻璃杯和一瓶干净的饮用水。他显得既兴奋又有些紧张。

【参考图片说明】
图1：本镜头的分镜设计图，请参考其构图、机位、光线、色调和整体氛围。
图2：胖橘猫的角色设计图，请严格参考其外观、服装、神态等视觉特征。

【镜头画面】
胖橘猫穿着特制的小围裙站在厨房里，面前摆放着一只透明玻璃杯和一瓶干净的饮用水。他显得既兴奋又有些紧张。

【镜头参数】
景别：中景 | 运镜：固定 | 时长：5.0秒

【台词】
"今天我们要学习的是如何正确地喝水。首先，选择一个合适的杯子非常重要。"

【连贯性提示】
后一镜：胖橘猫开始演示如何平稳地将水倒入杯子内...

【备注】
暖黄调，自然光线从窗户透入
```

**改进：** 新增的【参考图片说明】部分清楚地告诉 AI 模型：
- 图1 是分镜设计图，用于参考构图、光线、色调等
- 图2 是角色设计图，用于参考角色的外观特征

---

## 技术实现

### 1. VideoPromptBuilder.build_shot_prompt() 修改

新增 `reference_images` 参数，接收参考图片信息列表：

```python
@staticmethod
def build_shot_prompt(
    storyboard: Storyboard,
    scene: Scene | None = None,
    prev_shot: Storyboard | None = None,
    next_shot: Storyboard | None = None,
    reference_images: list[dict[str, str]] | None = None,  # 新增
) -> str:
    sections = []

    if scene:
        scene_context = VideoPromptBuilder._build_scene_context(scene)
        if scene_context:
            sections.append(f"【场景上下文】\n{scene_context}")

    # 新增：构建参考图片说明
    if reference_images:
        ref_desc = VideoPromptBuilder._build_reference_images_desc(reference_images)
        if ref_desc:
            sections.append(f"【参考图片说明】\n{ref_desc}")

    sections.append(f"【镜头画面】\n{storyboard.visual_content.strip()}")
    # ... 其余部分
```

### 2. 新增辅助方法 _build_reference_images_desc()

```python
@staticmethod
def _build_reference_images_desc(reference_images: list[dict[str, str]]) -> str:
    if not reference_images:
        return ""

    lines = []
    for i, ref in enumerate(reference_images, 1):
        ref_type = ref.get("type", "unknown")
        description = ref.get("description", "")

        if ref_type == "design":
            lines.append(f"图{i}：本镜头的分镜设计图，请参考其构图、机位、光线、色调和整体氛围。{description}")
        elif ref_type == "character":
            char_name = ref.get("character_name", "角色")
            lines.append(f"图{i}：{char_name}的角色设计图，请严格参考其外观、服装、神态等视觉特征。{description}")
        else:
            lines.append(f"图{i}：参考图片。{description}")

    return "\n".join(lines)
```

### 3. StoryboardBridge.batch_generate_videos() 修改

在调用 `build_shot_prompt()` 时，传递参考图片信息：

```python
reference_images_paths = []       # 用于 API 请求（文件路径列表）
reference_images_info = []        # 用于 prompt 说明（带类型和元数据）

# 添加分镜设计图
if shot.design_image:
    abs_path = to_absolute_path(shot.design_image, workspace_root)
    if abs_path:
        reference_images_paths.append(abs_path)
        reference_images_info.append({
            "type": "design",
            "description": ""
        })

# 添加角色设计图
visual_content = shot.visual_content or ""
for c in characters:
    if len(reference_images_paths) >= 5:
        break
    if c.design_image and (c.name in visual_content or c.ref_code in visual_content):
        abs_path = to_absolute_path(c.design_image, workspace_root)
        if abs_path:
            reference_images_paths.append(abs_path)
            reference_images_info.append({
                "type": "character",
                "character_name": c.name,
                "description": ""
            })

# 构建 prompt（传递参考图片信息）
prompt = VideoPromptBuilder.build_shot_prompt(
    shot, scene, prev_shot, next_shot, 
    reference_images=reference_images_info  # 新增
)

# 提交到 API（传递文件路径列表）
shot_list.append({
    "scene_number": shot.scene_number,
    "shot_number": shot.shot_number,
    "prompt": prompt,
    "project_id": project_id,
    "shot_id": shot.id,
    "reference_images": reference_images_paths,  # 使用路径列表
})
```

---

## 关键设计

1. **两个列表分离**：
   - `reference_images_paths`：存储文件绝对路径，用于 API 上传
   - `reference_images_info`：存储类型和元数据，用于生成 prompt 说明

2. **图片顺序保持一致**：
   - 图1 = 分镜设计图（如果有）
   - 图2-N = 角色设计图（按匹配顺序）

3. **Prompt 结构顺序**：
   - 【场景上下文】
   - **【参考图片说明】** ← 新增
   - 【镜头画面】
   - 【镜头参数】
   - 【台词】
   - 【音效】
   - 【连贯性提示】
   - 【备注】

4. **向后兼容**：
   - `reference_images` 参数默认为 `None`
   - 旧代码不传递该参数时，不会生成【参考图片说明】部分
