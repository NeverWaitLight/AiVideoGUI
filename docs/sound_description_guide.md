# 分镜声音描述功能指南

## 概述

本系统支持为分镜自动生成三类声音描述（文字形式），用于指导阿里万相等视频生成 AI 实现声画同步：

1. **content**（镜头内容）- 包含画面描述和**人物对话台词**
2. **sound_effect**（特殊音效）- 突出的、短暂的音效（脚步声、爆炸声、打雷声）
3. **ambient_sound**（环境背景音）- 持续存在的背景音（风声、雨声、木柴燃烧声）
4. **background_music**（背景音乐）- 烘托气氛的配乐（激昂、安静、恐怖等情绪）

这些声音描述由 AI 根据剧本内容和镜头画面自动生成，存储在数据库中，并在视频生成时传递给视频生成 API。

## 字段职责划分

### content（镜头内容）
**职责：** 画面描述 + 人物对话台词

**包含内容：**
- 人物动作、表情、姿态
- 场景环境、道具细节
- **人物对话台词**（用引号标注）
- **歌唱歌词**（如有）

**示例：**
```json
{
  "content": "{CHAR_A} 坐在桌前，表情严肃专注，嘴唇清晰地动着，低声说：'我们不能再装作一切没变。' {CHAR_B} 眼神略微低垂，安静地沉思。"
}
```

```json
{
  "content": "{CHAR_A} 站在舞台中央，闭眼轻声哼唱：'Follow the light, where the wild flowers grow'，微风吹动她的长发。"
}
```

### sound_effect（特殊音效）
**职责：** 突出的、短暂的、需要强调的音效

**不包括：** 人物对话（对话在 content 中）、持续的背景音（在 ambient_sound 中）

**常见类型：**
- 动作音效：脚步声、敲门声、关门声、玻璃破碎声、物体坠地
- 突发音效：爆炸声、打雷声、枪声、警报声、刹车声
- 机械音效：引擎启动、齿轮转动、金属碰撞、键盘敲击
- 自然音效：闪电劈裂、树枝折断、冰块碎裂、波浪拍打
- 特效音效：魔法施放、剑刃出鞘、8-bit游戏音效、电子故障

**示例：**
```json
{
  "sound_effect": "门突然被推开，发出吱呀声"
}
```

```json
{
  "sound_effect": "远处传来一声沉闷的爆炸声，震耳欲聋"
}
```

```json
{
  "sound_effect": "沉重的脚步声，靴子踩在湿滑地面上发出咔哒声"
}
```

### ambient_sound（环境背景音）
**职责：** 持续存在的、构成空间氛围感的背景声音

**特点：** 持续的、弥散的、构成环境基调的声音

**常见类型：**
- 自然环境：风声、雨声、流水声、海浪声、树叶沙沙、鸟鸣、虫鸣
- 室内环境：空调嗡鸣、钟表滴答、木柴燃烧噼啪、壁炉火焰、通风管道
- 城市环境：车流声、人群喧哗、地铁轰鸣、街头嘈杂、施工噪音
- 特殊空间：宇宙背景辐射白噪音、洞穴回声、水下气泡、森林静谧

**示例：**
```json
{
  "ambient_sound": "持续的风声，树叶沙沙作响，远处鸟儿鸣叫"
}
```

```json
{
  "ambient_sound": "持续的雨声，雨滴敲打地面和衣服，远处城市嗡鸣"
}
```

```json
{
  "ambient_sound": "木柴燃烧的噼啪声，壁炉火焰低沉嗡鸣"
}
```

### background_music（背景音乐）
**职责：** 烘托气氛、渲染情感的配乐

**常见类型：**
- 情绪氛围：激昂的音乐、安静的音乐、恐怖的音乐、悲伤的音乐、欢快的音乐
- 紧张悬疑：快速弦乐、不和谐音、心跳般鼓点、电子合成器不安音色
- 温馨浪漫：柔和钢琴、小提琴独奏、古典吉他、轻柔人声哼唱
- 史诗宏大：交响乐团、铜管齐奏、定音鼓震响、合唱团
- 卡点节奏：放克风格（鼓点清晰，贝斯律动）、电子舞曲、节奏明快流行乐

**示例：**
```json
{
  "background_music": "激昂的管弦乐，鼓点密集，渲染紧张气氛"
}
```

```json
{
  "background_music": "安静的钢琴旋律，舒缓柔和"
}
```

```json
{
  "background_music": "低沉不安的弦乐，营造恐怖氛围"
}
```

## 完整示例场景

### 示例 1：花园摘花（安静场景）

```json
{
  "scene_number": 1,
  "shot_number": 1,
  "shot_size": "close_up",
  "camera_movement": "固定镜头，聚焦于手部动作",
  "content": "日光，暖色调，侧光，特写镜头。{CHAR_A} 纤细的指尖轻轻捏住一片粉色玫瑰花瓣的边缘，以流畅而从容的动作，慢慢将其从花朵上摘下。",
  "sound_effect": "",
  "ambient_sound": "持续的风声，树叶沙沙作响，远处鸟儿鸣叫",
  "background_music": "柔和的木吉他音乐，旋律舒缓宁静",
  "duration": 6.0,
  "notes": "暖色调，阳光在皮肤上投下柔和的高光"
}
```

**说明：**
- **content**：只描述画面，无对话
- **sound_effect**：空（无突出音效）
- **ambient_sound**：持续的自然背景音
- **background_music**：温馨宁静的配乐

### 示例 2：餐厅对话（对话场景）

```json
{
  "scene_number": 1,
  "shot_number": 1,
  "shot_size": "medium_shot",
  "camera_movement": "固定镜头，双人对话构图",
  "content": "暖色调，日光透过大窗户，中景镜头。{CHAR_A} 坐在桌前，表情严肃专注，嘴唇清晰地动着，低声说：'我们不能再装作一切没变。' {CHAR_B} 眼神略微低垂，安静地沉思。",
  "sound_effect": "",
  "ambient_sound": "远处持续的街道车流声，室内安静",
  "background_music": "低沉的大提琴旋律，压抑而沉重，营造凝重气氛",
  "duration": 7.0,
  "notes": "暖色调，侧光突出人物表情"
}
```

**说明：**
- **content**：包含对话台词（用引号标注）
- **sound_effect**：空（对话不算特殊音效）
- **ambient_sound**：城市背景音
- **background_music**：凝重氛围的配乐

### 示例 3：雨夜街道（动作场景）

```json
{
  "scene_number": 1,
  "shot_number": 1,
  "shot_size": "full_shot",
  "camera_movement": "跟拍，跟随侦探行走",
  "content": "夜晚，冷蓝色调，霓虹灯光，全景镜头。{CHAR_A} 身穿黑色风衣和软呢帽，在雨中的街道上缓慢前行。雨水打湿了地面，霓虹灯光在湿滑的路面上反射。",
  "sound_effect": "沉重的脚步声，靴子踩在湿滑地面上发出咔哒声",
  "ambient_sound": "持续的雨声，雨滴敲打地面和衣服，远处城市嗡鸣",
  "background_music": "低沉的爵士乐，萨克斯独奏，营造神秘紧张的氛围",
  "duration": 6.0,
  "notes": "黑色电影风格，冷蓝色调"
}
```

**说明：**
- **content**：只描述画面和动作
- **sound_effect**：突出的脚步声（短暂、需强调）
- **ambient_sound**：持续的雨声和城市背景音
- **background_music**：神秘紧张的爵士乐

### 示例 4：爆炸场景（突发音效）

```json
{
  "scene_number": 1,
  "shot_number": 2,
  "shot_size": "medium_shot",
  "camera_movement": "固定镜头，正面拍摄",
  "content": "夜晚，冷蓝色调，中景镜头。{CHAR_A} 突然停下脚步，眼神警惕地望向远处。他的脸部半隐藏在帽檐阴影下，身体微微紧绷。",
  "sound_effect": "远处传来一声沉闷的爆炸声，震耳欲聋",
  "ambient_sound": "",
  "background_music": "音乐戛然而止，只剩爆炸后的回响",
  "duration": 4.0,
  "notes": "冷蓝色调，帽檐阴影强化神秘感"
}
```

**说明：**
- **content**：只描述画面和反应
- **sound_effect**：突发的爆炸声（短暂、强烈）
- **ambient_sound**：空（环境音被爆炸打断）
- **background_music**：音乐戛然而止的描述

## 数据库结构

### storyboard 表（分镜表）

```sql
CREATE TABLE storyboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id INTEGER NOT NULL,
    scene_number INTEGER NOT NULL,
    shot_number INTEGER NOT NULL,
    design_image VARCHAR(500) DEFAULT '',
    shot_size VARCHAR(50) DEFAULT 'medium_shot',
    camera_movement VARCHAR(255) DEFAULT '',
    content TEXT DEFAULT '',            -- 画面描述 + 人物对话
    sound_effect TEXT DEFAULT '',       -- 特殊音效（突出的、短暂的）
    ambient_sound TEXT DEFAULT '',      -- 环境背景音（持续的、弥散的）
    background_music TEXT DEFAULT '',   -- 背景音乐（烘托气氛）
    duration FLOAT DEFAULT 0.0,
    notes TEXT DEFAULT '',
    seed VARCHAR(255) DEFAULT '',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

### 场次级声音设定

剧本中的每个场次都包含 `sound_effect`、`ambient_sound`、`background_music` 三个声音字段。

### 分镜级声音继承

- 分镜默认继承所属场次的声音设定
- 如果该镜头的声音与场次保持一致，三个声音字段可以填空字符串（表示继承场次设定）
- 仅当镜头有特殊的声音变化时，才在对应字段中单独填写新的声音描述

### 示例

场次设定：
```json
{
  "scene_number": 1,
  "sound_effect": "",
  "ambient_sound": "城市嗡鸣声、车流声",
  "background_music": "轻快的钢琴曲"
}
```

镜头 1（继承场次设定）：
```json
{
  "scene_number": 1,
  "shot_number": 1,
  "sound_effect": "",
  "ambient_sound": "",
  "background_music": ""
}
```

镜头 2（切换到室内，环境音变化）：
```json
{
  "scene_number": 1,
  "shot_number": 2,
  "sound_effect": "",
  "ambient_sound": "室内安静，偶尔传来远处车流声",
  "background_music": ""
}
```

镜头 3（人物说话，音效变化）：
```json
{
  "scene_number": 1,
  "shot_number": 3,
  "sound_effect": "他低声说：'我们到了。'",
  "ambient_sound": "",
  "background_music": ""
}
```

## AI 生成流程

### 1. 提示词模板

位置：`prompts/templates/storyboard_generate.yaml`

模板中包含：
- 详细的声音字段说明
- 常见声音类型参考
- 填写要求和示例
- Few-shot 示例展示正确格式

### 2. LLM 生成

`TextPromptBuilder.build_storyboard_generation_messages()` 使用模板构建提示词，调用大语言模型生成分镜 JSON。

### 3. 解析入库

`ShotParser.parse()` 解析 JSON，提取 `sound_effect`、`ambient_sound`、`background_music` 三个字段。

### 4. 数据库存储

`ShotService` 将分镜数据保存到 `storyboard` 表。

## 视频生成时的使用

### 构建视频生成 Prompt

`VideoPromptBuilder.build_shot_prompt()` 自动整合声音描述到视频生成 Prompt：

```python
def build_shot_prompt(shot: Storyboard, scene: Scene, ...) -> str:
    sections = []
    
    # ... 其他部分 ...
    
    # 声音描述
    if shot.sound_effect:
        sections.append(f"【音效】{shot.sound_effect}")
    
    if shot.ambient_sound:
        sections.append(f"【环境音】{shot.ambient_sound}")
    
    if shot.background_music:
        sections.append(f"【背景音乐】{shot.background_music}")
    
    return "\n\n".join(sections)
```

### 传递给视频生成 API

阿里万相 2.5 API 支持在 `prompt` 中包含声音描述，AI 会根据文字生成匹配的音频。

示例 Prompt：
```
【场景上下文】第1场：室内-餐厅-日

【镜头画面】暖色调，日光透过大窗户，柔光，中景镜头，居中构图。{CHAR_A} 和 {CHAR_B} 在餐桌前对话...

【音效】{CHAR_A} 低声说："我们不能再装作一切没变。"

【环境音】远处传来模糊的街道车流声，室内安静

【背景音乐】低沉的大提琴旋律，压抑而沉重

【镜头参数】时长：7秒

【备注】暖色调，侧光突出人物表情
```

## 参考资料

- 阿里万相 2.5 Preview 版本声音生成文档
- `prompts/templates/storyboard_generate.yaml` - 提示词模板
- `prompts/video_prompt_builder.py` - 视频 Prompt 构建器
- `utils/shot_parser.py` - 分镜解析器
- `tests/test_shot_sound_fields.py` - 声音字段解析测试

## 版本历史

- **2026-08-06** - 初始版本，添加三个声音字段并优化提示词模板
