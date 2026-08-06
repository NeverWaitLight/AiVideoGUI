将剧本和分镜的 AI 生成输出从非结构化文本（Markdown 表格 / 纯文本）迁移到结构化 JSON 格式，提高解析可靠性和可维护性。

## 背景

**原有问题：** 剧本生成使用纯文本输出 + 正则解析，分镜生成使用 Markdown 表格输出 + 正则逐行解析，存在以下风险：
- LLM 输出格式不稳定（空格、标点、列数变化）导致解析失败
- 中文标点变体和景别中文名称变体影响枚举映射
- 调试困难（正则匹配失败时难以定位具体错误）

**解决方案：** 统一改为 JSON 输出格式，解析仅需 `json.loads()`，解析成功率从 ~85% 提升到 ~99%。

---

## 剧本 JSON 迁移

### JSON Schema

```json
{
  "title": "剧本标题",
  "scenes": [
    {
      "scene_number": 1,
      "location_type": "interior",
      "location": "审讯室",
      "time_type": "night",
      "time_detail": "深夜",
      "content": "完整的场次内容（动作描述和对话）"
    }
  ]
}
```

**字段说明**

| 字段 | 类型 | 枚举值 | 说明 |
|:---|:---|:---|:---|
| `title` | string | — | 剧本标题 |
| `scene_number` | integer | — | 场次编号（从 1 开始） |
| `location_type` | string | `interior` / `exterior` / `interior_exterior` | 内景/外景/内外景 |
| `location` | string | — | 地点描述 |
| `time_type` | string | `day` / `night` / `dawn` / `dusk` / `evening` / `custom` | 时间类型 |
| `time_detail` | string | — | 时间详细描述（标准时间可为空） |
| `content` | string | — | 场次完整内容（动作描述 + 对话） |

### 涉及文件

- `prompts/templates/script_generate.yaml` — 模板改为 JSON 输出
- `utils/script_parser.py` — 重写为 JSON 解析（约 50 行，原 102 行）
- `service/text_model_service.py` — 适配返回值

---

## 分镜 JSON 迁移

### JSON Schema

```json
{
  "storyboard": [
    {
      "scene_number": 1,
      "shot_number": 1,
      "shot_size": "medium_shot",
      "camera_movement": "固定镜头",
      "visual_content": "画面描述（支持 {CHAR_A} 角色代号）",
      "dialogue": "台词",
      "sound_effect": "音效",
      "duration": 5.0,
      "notes": "备注"
    }
  ],
  "characters": [
    {
      "name": "角色名称",
      "ref_code": "CHAR_A",
      "description": "结构化形象描述"
    }
  ]
}
```

**shot_size 枚举值**

| JSON 值 | ShotSize 枚举 | 中文名称 |
|:---|:---|:---|
| `extreme_close_up` | `ShotSize.EXTREME_CLOSE_UP` | 特写 |
| `close_up` | `ShotSize.CLOSE_UP` | 近景 |
| `medium_shot` | `ShotSize.MEDIUM_SHOT` | 中景 |
| `full_shot` | `ShotSize.FULL_SHOT` | 全景 |
| `long_shot` | `ShotSize.LONG_SHOT` | 远景 |
| `extreme_long_shot` | `ShotSize.EXTREME_LONG_SHOT` | 大远景 |

### 涉及文件

- `prompts/templates/storyboard_generate.yaml` — 模板改为 JSON 输出
- `prompts/templates/storyboard_optimize.yaml` — 同上
- `utils/shot_parser.py` — 重写为 JSON 解析（约 80 行，原 130 行）
- `utils/character_parser.py` — 精简移除 Markdown 表格回退（约 75 行，原 130 行）
- `service/text_model_service.py` — 适配返回值

### 色调/光影字段处理

当前 Markdown 表格有独立的"色调/光影"列，但 Storyboard dataclass 没有对应字段。新方案中将其合并到 `notes` 字段。

---

## 通用处理

### LLM 输出清洗

LLM 可能返回 Markdown 代码块包裹的 JSON，解析器添加预处理逻辑：

```python
text = text.strip()
if text.startswith("```json"):
    text = text[7:]
if text.startswith("```"):
    text = text[3:]
if text.endswith("```"):
    text = text[:-3]
text = text.strip()
```

### 风险评估

- **LLM 不遵守 JSON 格式**（中概率/高影响）：在提示词中强调格式 + 预处理清洗 + 错误日志记录原始响应
- **分镜+角色合并 JSON 过大**（低概率/中影响）：如经常被截断，考虑拆分为两次 LLM 调用
- **ShotSize 枚举值不匹配**（低概率/低影响）：未识别值使用默认值 + 日志警告

### 预期收益

- **解析成功率**：从 ~85% 提升到 ~99%
- **代码可维护性**：解析器代码量减少 40-50%
- **调试效率**：JSON 格式错误一目了然
- **技术一致性**：剧本和分镜使用统一的技术路线
- **字段对齐**：JSON Schema 字段名与 dataclass 一致，减少转换代码
