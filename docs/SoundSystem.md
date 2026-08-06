分镜声音描述功能支持为每个镜头生成三类声音描述（文字形式），用于指导阿里万相等视频生成 AI 实现声画同步。

## 声音字段职责

### content（镜头内容）

画面描述 + 人物对话台词。包含人物动作、表情、姿态、场景环境、道具细节，以及人物对话台词（用引号标注）和歌唱歌词。

**示例：**
- 无对话：`{CHAR_A} 纤细的指尖轻轻捏住一片花瓣...`
- 有对话：`{CHAR_A} 表情严肃，低声说：'我们不能再装作一切没变。'`

### sound_effect（特殊音效）

突出的、短暂的、需要强调的音效。**不包括**人物对话（在 content 中）和持续的背景音（在 ambient_sound 中）。

**常见类型：**
- **动作音效：** 脚步声、敲门声、关门声、玻璃破碎
- **突发音效：** 爆炸声、打雷声、枪声、警报声
- **机械音效：** 引擎启动、齿轮转动、键盘敲击
- **特效音效：** 魔法施放、剑刃出鞘、8-bit 音效

### ambient_sound（环境背景音）

持续存在的、构成空间氛围感的背景声音。特点是持续的、弥散的、构成环境基调。

**常见类型：**
- **自然环境：** 风声、雨声、流水声、树叶沙沙、鸟鸣
- **室内环境：** 空调嗡鸣、钟表滴答、木柴燃烧噼啪
- **城市环境：** 车流声、人群喧哗、地铁轰鸣

### background_music（背景音乐）

烘托气氛、渲染情感的配乐。

**常见类型：**
- **情绪氛围：** 激昂、安静、恐怖、悲伤、欢快、紧张
- **乐器类型：** 钢琴独奏、交响乐团、电子合成器
- **节奏特征：** 节奏缓慢、鼓点密集、旋律渐强

## 完整示例场景

### 花园摘花（安静场景）

```json
{
  "content": "{CHAR_A} 纤细的指尖轻轻捏住一片粉色玫瑰花瓣...",
  "sound_effect": "",
  "ambient_sound": "持续的风声，树叶沙沙作响，远处鸟儿鸣叫",
  "background_music": "柔和的木吉他音乐，旋律舒缓宁静"
}
```

### 餐厅对话（对话场景）

```json
{
  "content": "{CHAR_A} 坐在桌前，表情严肃专注，低声说：'我们不能再装作一切没变。'",
  "sound_effect": "",
  "ambient_sound": "远处持续的街道车流声，室内安静",
  "background_music": "低沉的大提琴旋律，压抑而沉重"
}
```

### 雨夜街道（动作 + 突发音效）

```json
{
  "content": "{CHAR_A} 身穿黑色风衣，在雨中的街道上缓慢前行。",
  "sound_effect": "沉重的脚步声，靴子踩在湿滑地面上发出咔哒声",
  "ambient_sound": "持续的雨声，雨滴敲打地面和衣服，远处城市嗡鸣",
  "background_music": "低沉的爵士乐，萨克斯独奏"
}
```

## 声音继承规则

### 场次级别

剧本中的每个场次包含 `sound_effect`、`ambient_sound`、`background_music` 三个声音字段，定义该场次的默认声音设定。

### 分镜级别

- 分镜默认继承所属场次的声音设定
- 如果声音与场次一致，字段填空字符串
- 仅当声音有变化时，才在对应字段中填写新的描述

## 视频生成时的 Prompt 整合

`VideoPromptBuilder.build_shot_prompt()` 自动将声音描述整合到视频生成 Prompt，顺序如下：

1. 【场景上下文】
2. 【视觉风格】
3. 【参考图片说明】
4. 【镜头画面】
5. 【镜头参数】
6. **【音效】**
7. **【环境音】**
8. **【背景音乐】**
9. 【连贯性提示】
10. 【备注】

## 实现细节

### 数据流

```
AI 生成分镜（storyboard_generate.yaml 模板）
  → LLM 返回 JSON（包含声音字段）
  → ShotParser 解析（提取三个声音字段）
  → 保存到数据库（storyboard 表）
  → 视频生成时 VideoPromptBuilder 整合到 Prompt
  → 传递给视频生成 API
```

### 数据库

`storyboard` 表包含 `content`、`sound_effect`、`ambient_sound`、`background_music` 四个字段。原有 `dialogue` 字段已删除（对话合并到 `content` 中）。

### 涉及文件

- `prompts/templates/storyboard_generate.yaml` — 声音字段说明和 Few-shot 示例
- `utils/shot_parser.py` — 提取三个声音字段
- `prompts/video_prompt_builder.py` — 整合声音到 Prompt
- `tests/test_shot_sound_fields.py` — 解析器测试
- `tests/test_video_prompt_sound.py` — Prompt 构建器测试

### 字段职责变更历史

声音字段经历了一次重要的职责重新定义：

- **变更前**：`sound_effect` 包含人物对话，`content` 仅包含画面描述
- **变更后**：对话移到 `content` 中，`sound_effect` 仅用于突出的、短暂的特殊音效

变更仅涉及提示词模板和文档，不影响代码逻辑和数据库结构。
