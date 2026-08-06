# 分镜声音描述功能实现总结

## 修改时间
2026-08-06

## 实现目标
为分镜生成系统添加完整的声音描述功能，参考阿里万相 2.5 的声音生成能力，支持三类声音描述：
1. **sound_effect**（音效）- 人物对话、动作音效、环境音效
2. **ambient_sound**（环境音）- 自然环境、城市环境、特定空间
3. **background_music**（背景音乐）- 情绪音乐、卡点音乐、轻音乐

## 修改内容

### 1. 解析器修复（`utils/shot_parser.py`）

**问题：** 解析器只提取了 `sound_effect` 字段，缺少 `ambient_sound` 和 `background_music`

**修复：** 在 `_parse_shots()` 方法中添加两个字段的提取：
```python
shots.append({
    # ... 其他字段 ...
    "sound_effect": shot.get("sound_effect", ""),
    "ambient_sound": shot.get("ambient_sound", ""),      # 新增
    "background_music": shot.get("background_music", ""), # 新增
    "duration": float(shot.get("duration", 0.0)),
    "notes": shot.get("notes", ""),
})
```

### 2. 提示词模板优化（`prompts/templates/storyboard_generate.yaml`）

**修改内容：**

#### 2.1 扩展字段说明

为三个声音字段添加了详细的说明和示例：

**sound_effect（音效）：**
- 人声类：对话内容（含具体台词）、独白、耳语、歌唱（含歌词）
- 动作音效：脚步声、敲门声、物体坠地、撞击声、键盘声
- 环境音效：火焰燃烧、动物叫声、电子音效、ASMR
- 游戏/机械音效：8-bit 音效、故障声、电流嗡鸣

填写要求：
- 对话必须写明具体台词，用引号标注
- 歌唱必须包含歌词片段
- 音效需具体到声音特征和节奏

**ambient_sound（环境音）：**
- 自然环境：树叶沙沙、鸟鸣、风声、流水声
- 城市环境：车流声、人群嗡鸣、列车轰鸣
- 特定空间：室内回声、宇宙背景辐射、金属形变声

填写要求：
- 与场景地点和时间相匹配
- 可描述声音的空间感（"远处传来""模糊不清的"）
- 可组合多个环境音

**background_music（背景音乐）：**
- 情绪音乐：温馨快乐、紧张悬疑、悲伤忧郁、史诗宏大
- 卡点音乐：放克风格、电子舞曲、节奏明快
- 轻音乐：钢琴旋律、木吉他、古典弦乐、爵士乐
- 特定风格：8-bit 游戏、复古合成波、管弦乐

填写要求：
- 描述音乐风格和情绪
- 可描述节奏变化和乐器类型

#### 2.2 添加 Few-shot 示例

添加了两个完整的示例，展示如何正确填写声音描述：

**示例 1：花园摘花场景**
- 环境音：树叶沙沙声、鸟鸣、风声
- 背景音乐：柔和的木吉他音乐

**示例 2：餐厅对话场景**
- 音效：具体台词（"我们不能再装作一切没变。""但如果遗忘比记住更痛怎么办？"）
- 环境音：远处街道车流声，室内安静
- 背景音乐：低沉的大提琴旋律，压抑而沉重

### 3. 视频 Prompt 构建器修复（`prompts/video_prompt_builder.py`）

**问题：** 
1. 只整合了 `sound_effect`，缺少 `ambient_sound` 和 `background_music`
2. 引用了已删除的 `dialogue` 字段

**修复：**
```python
# 移除 dialogue 字段引用
# if storyboard.dialogue and storyboard.dialogue.strip():
#     sections.append(f"【台词】\n{storyboard.dialogue.strip()}")

# 添加环境音和背景音乐
if storyboard.ambient_sound and storyboard.ambient_sound.strip():
    sections.append(f"【环境音】\n{storyboard.ambient_sound.strip()}")

if storyboard.background_music and storyboard.background_music.strip():
    sections.append(f"【背景音乐】\n{storyboard.background_music.strip()}")
```

**Prompt 结构（按顺序）：**
1. 【场景上下文】
2. 【视觉风格】
3. 【参考图片说明】
4. 【镜头画面】
5. 【镜头参数】
6. 【音效】
7. 【环境音】
8. 【背景音乐】
9. 【连贯性提示】
10. 【备注】

### 4. 测试用例

#### 4.1 解析器测试（`tests/test_shot_sound_fields.py`）

- `test_parse_all_sound_fields` - 验证三个声音字段都能正确提取
- `test_parse_empty_sound_fields` - 验证空字段处理（继承场次设定）
- `test_parse_dialogue_with_sound_effects` - 验证对话和音效同时处理
- `test_parse_missing_sound_fields` - 验证向后兼容（缺失字段填充空字符串）

#### 4.2 视频 Prompt 构建器测试（`tests/test_video_prompt_sound.py`）

- `test_build_prompt_with_all_sound_fields` - 验证所有声音字段都出现在 Prompt 中
- `test_build_prompt_with_empty_sound_fields` - 验证空字段不出现在 Prompt 中
- `test_build_prompt_with_partial_sound_fields` - 验证部分字段处理
- `test_sound_fields_order_in_prompt` - 验证声音字段的顺序

**测试结果：** 所有 17 个测试全部通过 ✅

### 5. 文档

创建了两份文档：
- `docs/sound_description_guide.md` - 完整的声音描述功能指南
- `docs/sound_implementation_summary.md` - 本次实现总结（本文档）

## 数据流程

```
用户创建项目 → 编写剧本（场次包含声音设定）
    ↓
AI 生成分镜（TextPromptBuilder + storyboard_generate.yaml）
    ↓
LLM 返回 JSON（包含 sound_effect、ambient_sound、background_music）
    ↓
ShotParser 解析 JSON（提取所有声音字段）
    ↓
ShotService 保存到数据库（storyboard 表）
    ↓
用户批量生成视频
    ↓
VideoPromptBuilder 构建 Prompt（整合所有声音描述）
    ↓
视频生成 API（阿里万相 2.5 根据文字生成声音）
```

## 声音继承规则

### 场次级别
剧本中的每个场次包含三个声音字段，定义该场次的默认声音设定。

### 分镜级别
- 分镜默认继承所属场次的声音设定
- 如果声音与场次一致，字段填空字符串
- 仅当声音有变化时，才在对应字段中填写新的描述

### 示例

**场次设定：**
```json
{
  "scene_number": 1,
  "ambient_sound": "城市嗡鸣声、车流声",
  "background_music": "轻快的钢琴曲"
}
```

**镜头 1（继承）：**
```json
{
  "scene_number": 1,
  "shot_number": 1,
  "sound_effect": "",
  "ambient_sound": "",
  "background_music": ""
}
```

**镜头 2（环境音变化）：**
```json
{
  "scene_number": 1,
  "shot_number": 2,
  "sound_effect": "",
  "ambient_sound": "室内安静，偶尔传来远处车流声",
  "background_music": ""
}
```

## 兼容性

### 向后兼容
- 解析器支持缺失字段（自动填充空字符串）
- 旧数据库迁移已完成（`dialogue` 字段已删除，三个声音字段已存在）

### 数据库状态
- ✅ `storyboard` 表包含三个声音字段
- ✅ `storyboard_history` 表包含三个声音字段
- ✅ 数据模型（`Storyboard`）包含三个声音字段
- ❌ `dialogue` 字段已从数据库和模型中删除

## 使用阿里万相 API

参考文档中的示例，Prompt 格式为：

```
【场景上下文】第1场：室内-餐厅-日

【镜头画面】暖色调，日光透过大窗户，柔光，中景镜头，居中构图。{CHAR_A} 和 {CHAR_B} 在餐桌前对话...

【音效】{CHAR_A} 低声说："我们不能再装作一切没变。"

【环境音】远处传来模糊的街道车流声，室内安静

【背景音乐】低沉的大提琴旋律，压抑而沉重

【镜头参数】景别：中景 | 运镜：固定镜头

【备注】暖色调，侧光突出人物表情
```

阿里万相 2.5 API 会根据 Prompt 中的声音描述，自动生成匹配的音频（人声、环境音、背景音乐）并与视频同步。

## 参考资料

- 阿里万相 2.5 Preview 版本声音生成文档（用户提供）
- `prompts/templates/storyboard_generate.yaml` - 提示词模板
- `prompts/video_prompt_builder.py` - 视频 Prompt 构建器
- `utils/shot_parser.py` - 分镜解析器
- `docs/sound_description_guide.md` - 声音描述功能指南

## 后续优化建议

1. **UI 界面支持** - 在分镜编辑页面添加三个声音字段的输入框
2. **声音预设库** - 提供常用声音描述模板（如"咖啡厅环境音""紧张悬疑配乐"）
3. **智能推荐** - 根据场景类型和情绪自动推荐合适的声音描述
4. **批量编辑** - 支持批量修改多个镜头的声音设定
5. **声音预览** - 在 UI 中展示声音描述的效果预览

## 总结

本次修改完整实现了分镜声音描述功能：
- ✅ 修复了解析器缺失字段的问题
- ✅ 优化了提示词模板，添加详细的声音类型参考和 few-shot 示例
- ✅ 修复了视频 Prompt 构建器，整合所有声音字段
- ✅ 移除了已废弃的 `dialogue` 字段引用
- ✅ 创建了完整的测试用例（17 个测试全部通过）
- ✅ 编写了详细的功能文档

用户现在可以：
1. 在剧本中为每个场次设定默认声音
2. 在分镜生成时，AI 自动为每个镜头生成声音描述
3. 在视频生成时，声音描述会整合到 Prompt 中，传递给阿里万相 API
4. 阿里万相 2.5 根据文字描述自动生成匹配的音频（人声、环境音、背景音乐）

这为用户提供了一个完整的"文字 → 画面 + 声音"的视频生成流程，大幅提升了生成视频的表现力和沉浸感。
