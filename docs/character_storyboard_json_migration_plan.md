# 角色和分镜 AI 生成结构化数据入库方案

## 📋 背景

**当前问题：** 分镜生成（`storyboard_generate.yaml`）和分镜优化（`storyboard_optimize.yaml`）模板使用 Markdown 表格输出格式，`ShotParser` 通过正则表达式逐行解析，存在以下风险：

1. LLM 输出的 Markdown 表格格式不稳定（列数不对齐、换行丢失）导致解析失败
2. 景别中文名称变体（如"面部特写"vs"特写"）影响枚举映射
3. `ShotParser.parse_characters()` 依赖文本结构解析角色表，容易受格式波动影响
4. 分镜与角色合并在一次 LLM 调用中输出，解析逻辑耦合在一起
5. 调试困难（正则匹配失败时难以定位具体是哪行哪列出错）

**角色生成已完成迁移：** `character_generate.yaml` 和 `character_optimize.yaml` 已使用 JSON 输出格式，`CharacterParser` 已支持 JSON 解析。本方案仅对 `CharacterParser` 做精简优化（移除不必要的 Markdown 表格回退逻辑）。

**解决方案：** 将分镜生成模板改为输出结构化 JSON 格式，与已完成的 `script_json_migration_plan.md` 保持一致的技术路线。

---

## 🔍 现状分析

### 分镜生成现状

**模板文件：** `prompts/templates/storyboard_generate.yaml`
- 输出格式：Markdown 表格（8 列：场次、镜头序号、景别、画面内容描述、运镜方式、音效/台词、时长(秒)、色调/光影）
- 同时输出角色设计表（第二个 Markdown 表格）
- 一次 LLM 调用产生两段表格

**解析器：** `utils/shot_parser.py`（约 130 行）
- `parse()` 方法：正则逐行解析 Markdown 表格，通过 `|` 分隔列，用中文键名映射
- `parse_characters()` 方法：解析第二个角色设计表
- `SHOT_SIZE_MAP`：中文 → ShotSize 枚举映射（6 项）
- 风险点：列数不足时整行跳过、`re.search(r"\d+", cells[0])` 提取数字可能匹配错误

**分镜优化模板：** `prompts/templates/storyboard_optimize.yaml`
- 同样使用 Markdown 表格格式
- 仅输出分镜表（不含角色表）
- 解析也走 `ShotParser.parse()`

### 角色生成现状（已完成 JSON 迁移）

**模板文件：** `prompts/templates/character_generate.yaml`、`character_optimize.yaml`
- 已输出 JSON 数组格式：`[{"name": "...", "ref_code": "...", "description": "..."}]`
- `CharacterParser` 已支持 JSON 解析

**解析器：** `utils/character_parser.py`（约 130 行）
- 支持 JSON + Markdown 表格双格式回退
- 存在冗余代码（`_parse_markdown_table()` 方法），因为模板已不再输出 Markdown 表格
- 字段名约定：`name`、`ref_code`、`description`（与 Character dataclass 一致）

### 数据模型现状

**Storyboard dataclass** (`models/storyboard.py`)：
```python
@dataclass
class Storyboard:
    scene_number: int
    shot_number: int
    id: int = 0
    scene_id: int = 0
    design_image: str = ""
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT
    camera_movement: str = ""
    visual_content: str = ""
    dialogue: str = ""
    sound_effect: str = ""
    duration: float = 0.0
    notes: str = ""
    seed: str = ""
    created_at: int = 0
    updated_at: int = 0
```

**ShotSize 枚举** (`models/enums.py`)：
```python
class ShotSize(enum.Enum):
    EXTREME_CLOSE_UP = "extreme_close_up"
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    FULL_SHOT = "full_shot"
    LONG_SHOT = "long_shot"
    EXTREME_LONG_SHOT = "extreme_long_shot"
```

**Character dataclass** (`models/character.py`)：
```python
@dataclass
class Character:
    id: int
    uuid: str
    project_id: int
    name: str
    ref_code: str
    design_image: str = ""
    description: str = ""
    created_at: int = 0
    updated_at: int = 0
```

### 调用链路

```
分镜生成：
  StoryboardBridge → StoryboardGenerateWorker → TextModelService.generate_storyboard()
    → TextPromptBuilder.build_storyboard_generation_messages()
    → LLM 返回 Markdown 表格
    → ShotParser.parse() + ShotParser.parse_characters()
    → 返回 {"shots": [...], "characters": [...]}

分镜优化：
  StoryboardBridge → StoryboardOptimizeWorker → TextModelService.optimize_storyboard()
    → TextPromptBuilder.build_storyboard_optimization_messages()
    → LLM 返回 Markdown 表格
    → ShotParser.parse()
    → 返回 shots 列表

角色生成（已完成）：
  CharacterBridge → CharacterWorker → TextModelService.generate_characters()
    → TextPromptBuilder.build_character_generation_messages()
    → LLM 返回 JSON
    → CharacterParser.parse()
    → 返回 characters 列表
```

---

## ✅ 改进方案

### 目标

1. **可靠性** — JSON 格式解析 100% 成功率（仅需 `json.loads()`）
2. **可维护性** — 无需维护正则表达式和列索引映射
3. **字段对齐** — JSON Schema 字段名与 Storyboard / Character dataclass 一致，减少映射代码
4. **可调试性** — JSON 格式错误一目了然
5. **与剧本迁移保持一致** — 复用已验证的 Markdown 代码块清洗模式

---

## 📐 分镜生成 JSON Schema

### JSON 结构设计

```json
{
  "storyboard": [
    {
      "scene_number": 1,
      "shot_number": 1,
      "shot_size": "medium_shot",
      "camera_movement": "固定镜头",
      "visual_content": "警察坐在审讯室的桌前，眼神犀利地盯着对面的嫌疑人。房间灯光昏暗，气氛紧张。",
      "dialogue": "警察：你知道自己在做什么吗？",
      "sound_effect": "椅子摩擦地面的声音",
      "duration": 5.0,
      "notes": ""
    },
    {
      "scene_number": 1,
      "shot_number": 2,
      "shot_size": "close_up",
      "camera_movement": "缓慢推进",
      "visual_content": "{CHAR_A} 低头不语，面色凝重，双手紧握。",
      "dialogue": "",
      "sound_effect": "低沉的背景音乐",
      "duration": 4.0,
      "notes": "注意 {CHAR_A} 的面部表情特写"
    }
  ],
  "characters": [
    {
      "name": "李探长",
      "ref_code": "CHAR_A",
      "description": "[物种] 人类-黄种人\n[外貌] 45岁男性，国字脸，目光锐利\n[发型] 短发\n[发色] 黑色带少许白发\n[瞳色] 深褐色\n[体型] 魁梧，身高178cm"
    }
  ]
}
```

### 字段说明

**`storyboard` 数组：**

| 字段 | 类型 | 说明 | 是否必填 | 对应 dataclass 字段 |
|:---|:---|:---|:---|:---|
| `scene_number` | integer | 场次编号 | 是 | `Storyboard.scene_number` |
| `shot_number` | integer | 镜号（每场从 1 开始） | 是 | `Storyboard.shot_number` |
| `shot_size` | string | 景别枚举值 | 是 | `Storyboard.shot_size` |
| `camera_movement` | string | 运镜方式 | 是 | `Storyboard.camera_movement` |
| `visual_content` | string | 画面描述（支持 `{CHAR_A}` 角色代号） | 是 | `Storyboard.visual_content` |
| `dialogue` | string | 台词（可为空） | 否 | `Storyboard.dialogue` |
| `sound_effect` | string | 音效（可为空） | 否 | `Storyboard.sound_effect` |
| `duration` | number | 时长（秒） | 是 | `Storyboard.duration` |
| `notes` | string | 备注（可为空） | 否 | `Storyboard.notes` |

**`characters` 数组：**

| 字段 | 类型 | 说明 | 是否必填 | 对应 dataclass 字段 |
|:---|:---|:---|:---|:---|
| `name` | string | 角色名称 | 是 | `Character.name` |
| `ref_code` | string | 引用代号（CHAR_A, CHAR_B...） | 是 | `Character.ref_code` |
| `description` | string | 结构化形象描述 | 是 | `Character.description` |

### shot_size 枚举值映射

| JSON 值 | ShotSize 枚举 | 中文名称 |
|:---|:---|:---|
| `extreme_close_up` | `ShotSize.EXTREME_CLOSE_UP` | 特写 |
| `close_up` | `ShotSize.CLOSE_UP` | 近景 |
| `medium_shot` | `ShotSize.MEDIUM_SHOT` | 中景 |
| `full_shot` | `ShotSize.FULL_SHOT` | 全景 |
| `long_shot` | `ShotSize.LONG_SHOT` | 远景 |
| `extreme_long_shot` | `ShotSize.EXTREME_LONG_SHOT` | 大远景 |

> **注意：** 与当前 `ShotParser.SHOT_SIZE_MAP` 的中文键不同，JSON Schema 使用英文枚举值，与 `ShotSize.value` 一致，解析器直接用字符串匹配枚举值，无需再维护中文映射表。

---

## 🛠️ 实施步骤

### Step 1: 修改分镜生成 YAML 模板

**文件：** `prompts/templates/storyboard_generate.yaml`

**修改内容：**
- 将 system_prompt 中的 Markdown 表格格式要求替换为 JSON 格式要求
- 保留分镜创作原则（第二步 ~ 第四步）
- 保留角色设计表要求（第五步），但改为 JSON 输出
- 删除 `| 场次 | 镜头序号 | ...` 等表格列定义
- 新增 JSON Schema 示例和字段说明

**关键变更：**
```yaml
# 旧版（Markdown 表格格式）
第三步：生成结构化分镜表格
| 场次 | 镜头序号 | 景别 | 画面内容描述 | 运镜方式 | 音效/台词 | 时长(秒) | 色调/光影 |

第五步：输出角色设计表
| 角色名 | 引用代号 | 形象描述 |

# 新版（JSON 格式）
第三步：输出 JSON 格式
必须输出严格的 JSON 格式，结构如下：
{
  "storyboard": [
    {
      "scene_number": 1,
      "shot_number": 1,
      "shot_size": "medium_shot",
      "camera_movement": "固定镜头",
      "visual_content": "画面描述",
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

字段说明：
- shot_size 必须是以下枚举值之一：
  "extreme_close_up"(特写) / "close_up"(近景) / "medium_shot"(中景)
  "full_shot"(全景) / "long_shot"(远景) / "extreme_long_shot"(大远景)
- visual_content 可使用 {CHAR_A} 等角色代号引用角色
- 色调/光影信息合并到 notes 字段中

直接输出 JSON，不要添加任何 Markdown 代码块标记或其他说明。
```

**色调/光影字段处理：** 当前 Markdown 表格有独立的"色调/光影"列，但 Storyboard dataclass 没有对应字段。新方案中将其合并到 `notes` 字段，格式为 `"[色调] 冷蓝调，侧逆光\n[备注] 其他备注"`，或直接追加到 notes 末尾。

---

### Step 2: 修改分镜优化 YAML 模板

**文件：** `prompts/templates/storyboard_optimize.yaml`

**修改内容：** 与 Step 1 类似，将 Markdown 表格输出改为 JSON 输出。注意优化模板不输出角色表（只有 `storyboard` 数组）。

**关键变更：**
```yaml
system_prompt: |
  你是一位专业的电影导演兼分镜师。根据用户要求优化分镜头脚本。

  输出严格的 JSON 格式：
  {
    "storyboard": [
      {
        "scene_number": 1,
        "shot_number": 1,
        "shot_size": "medium_shot",
        "camera_movement": "固定镜头",
        "visual_content": "画面描述",
        "dialogue": "台词",
        "sound_effect": "音效",
        "duration": 5.0,
        "notes": "备注"
      }
    ]
  }

  字段说明：（同 Step 1）

  优化要求：
  1. 保持场次编号与剧本对应
  2. 画面描述高度具体、可视化
  3. shot_size 和 camera_movement 精准标注
  4. 全片视觉风格统一

  直接输出 JSON，不要添加任何 Markdown 代码块标记或其他说明。
```

---

### Step 3: 重写 ShotParser

**文件：** `utils/shot_parser.py`

**修改策略：** 完全重写，从 Markdown 表格解析改为 JSON 解析。移除 `parse_characters()` 方法（角色数据合并到 `parse()` 的返回值中）。

**新实现：**
```python
"""分镜数据解析器"""

import json
from loguru import logger
from typing import Any

from models.enums import ShotSize


class ShotParser:
    SHOT_SIZE_MAP = {
        "extreme_close_up": ShotSize.EXTREME_CLOSE_UP,
        "close_up": ShotSize.CLOSE_UP,
        "medium_shot": ShotSize.MEDIUM_SHOT,
        "full_shot": ShotSize.FULL_SHOT,
        "long_shot": ShotSize.LONG_SHOT,
        "extreme_long_shot": ShotSize.EXTREME_LONG_SHOT,
    }

    @classmethod
    def parse(cls, storyboard_json: str) -> dict[str, list[dict[str, Any]]]:
        """解析 JSON 格式的分镜数据

        Returns:
            {"shots": [...], "characters": [...]}
        """
        # 清洗 Markdown 代码块标记
        storyboard_json = storyboard_json.strip()
        if storyboard_json.startswith("```json"):
            storyboard_json = storyboard_json[7:]
        if storyboard_json.startswith("```"):
            storyboard_json = storyboard_json[3:]
        if storyboard_json.endswith("```"):
            storyboard_json = storyboard_json[:-3]
        storyboard_json = storyboard_json.strip()

        try:
            data = json.loads(storyboard_json)
        except json.JSONDecodeError as e:
            logger.error(f"分镜 JSON 解析失败: {e}")
            logger.error(f"原始文本:\n{storyboard_json[:500]}")
            raise ValueError(f"无效的 JSON 格式: {e}")

        shots = cls._parse_shots(data.get("storyboard", []))
        characters = cls._parse_characters(data.get("characters", []))

        logger.info(f"解析分镜完成：共 {len(shots)} 个镜头，{len(characters)} 个角色")
        return {"shots": shots, "characters": characters}

    @classmethod
    def _parse_shots(cls, shots_raw: list[dict]) -> list[dict[str, Any]]:
        shots = []
        for shot in shots_raw:
            shot_size_str = shot.get("shot_size", "medium_shot")
            shot_size_enum = cls.SHOT_SIZE_MAP.get(shot_size_str, ShotSize.MEDIUM_SHOT)
            if shot_size_str not in cls.SHOT_SIZE_MAP:
                logger.warning(f"未识别的景别值 '{shot_size_str}'，使用默认值 medium_shot")

            shots.append({
                "scene_number": shot.get("scene_number", 0),
                "shot_number": shot.get("shot_number", 0),
                "shot_size": shot_size_enum.value,
                "camera_movement": shot.get("camera_movement", ""),
                "visual_content": shot.get("visual_content", ""),
                "dialogue": shot.get("dialogue", ""),
                "sound_effect": shot.get("sound_effect", ""),
                "duration": float(shot.get("duration", 0.0)),
                "notes": shot.get("notes", ""),
            })
        return shots

    @classmethod
    def _parse_characters(cls, characters_raw: list[dict]) -> list[dict[str, Any]]:
        characters = []
        for char in characters_raw:
            name = char.get("name", "").strip()
            ref_code = char.get("ref_code", "").strip()
            description = char.get("description", "").strip()
            if not name or not ref_code:
                logger.warning(f"跳过无效角色数据: {char}")
                continue
            characters.append({
                "name": name,
                "ref_code": ref_code,
                "description": description,
            })
        return characters
```

**代码量对比：**
- 旧版：约 130 行（正则表达式 + 逐行解析 + 角色表解析）
- 新版：约 80 行（JSON 解析 + 枚举映射 + 角色提取）

---

### Step 4: 更新 TextModelService 调用

**文件：** `service/text_model_service.py`

**涉及方法：**

#### 4.1 `generate_storyboard()` — 无需大改

当前返回 `{"shots": [...], "characters": [...]}` 字典，新的 `ShotParser.parse()` 返回相同结构，无需修改调用方。

```python
# 现有代码（无需修改）
from utils.shot_parser import ShotParser
result = ShotParser.parse(storyboard_content)  # 返回 {"shots": [...], "characters": [...]}
return result
```

#### 4.2 `optimize_storyboard()` — 适配返回值

当前只返回 shots 列表，新的 `ShotParser.parse()` 返回字典。需要适配：

```python
# 旧版
shots = ShotParser.parse(result)
return shots

# 新版
parse_result = ShotParser.parse(result)
return parse_result["shots"]  # 优化模式下忽略 characters
```

---

### Step 5: 更新 Bridge 层调用

**文件：** `bridge/characters_bridge.py` 和 `bridge/storyboard_bridge.py`

检查 `StoryboardBridge` 中调用 `generate_storyboard()` 结果后入库的逻辑，确保字段名与新解析器输出一致。

**关键字段映射检查：**

| 解析器输出字段 | Storyboard dataclass 字段 | 是否一致 |
|:---|:---|:---|
| `scene_number` | `scene_number` | ✅ |
| `shot_number` | `shot_number` | ✅ |
| `shot_size` (string) | `shot_size` (ShotSize enum) | 需转换 |
| `camera_movement` | `camera_movement` | ✅ |
| `visual_content` | `visual_content` | ✅ |
| `dialogue` | `dialogue` | ✅ |
| `sound_effect` | `sound_effect` | ✅ |
| `duration` | `duration` | ✅ |
| `notes` | `notes` | ✅ |

> `shot_size` 在解析器输出中是字符串值（如 `"medium_shot"`），Bridge 层入库时需要转为 `ShotSize` 枚举。这个转换在现有代码中已经存在，不需要修改。

---

### Step 6: 精简 CharacterParser

**文件：** `utils/character_parser.py`

**修改策略：** 因为模板已不再输出 Markdown 表格格式，可以移除 `_parse_markdown_table()` 和相关辅助方法。但保留 JSON 代码块提取逻辑（处理 LLM 返回 Markdown 包裹的 JSON）。

**精简后的实现：**
```python
"""角色数据解析器"""

import json
import re
from loguru import logger


class CharacterParser:
    """解析 LLM 返回的角色数据"""

    @staticmethod
    def parse(response_text: str) -> list[dict]:
        """解析 JSON 格式的角色列表

        Args:
            response_text: LLM 返回的原始文本（JSON 数组或 {"characters": [...]} 对象）

        Returns:
            角色列表，每个角色包含 name, ref_code, description 字段

        Raises:
            ValueError: 解析失败时抛出
        """
        response_text = response_text.strip()

        # 清洗 Markdown 代码块标记
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # 尝试直接解析 JSON
        characters = CharacterParser._try_parse_json(response_text)
        if characters is not None:
            logger.info(f"解析角色完成：共 {len(characters)} 个角色")
            return characters

        # 尝试从文本中提取 JSON 块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            characters = CharacterParser._try_parse_json(json_match.group(1))
            if characters is not None:
                logger.info(f"从代码块中提取角色完成：共 {len(characters)} 个角色")
                return characters

        # 尝试查找 JSON 数组或对象
        json_match = re.search(r'[\[{][\s\S]*[\]}]', response_text)
        if json_match:
            characters = CharacterParser._try_parse_json(json_match.group(0))
            if characters is not None:
                logger.info(f"从文本中提取角色完成：共 {len(characters)} 个角色")
                return characters

        logger.error(f"无法解析角色数据，原始文本:\n{response_text[:500]}")
        raise ValueError("无法解析角色数据，格式不正确")

    @staticmethod
    def _try_parse_json(text: str) -> list[dict] | None:
        """尝试解析 JSON，返回角色列表或 None"""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "characters" in data:
            items = data["characters"]
        else:
            return None

        return CharacterParser._validate_characters(items)

    @staticmethod
    def _validate_characters(data: list[dict]) -> list[dict]:
        """验证并规范化角色数据"""
        validated = []
        for item in data:
            if not isinstance(item, dict):
                continue

            name = (item.get("name") or item.get("角色名") or "").strip()
            ref_code = (item.get("ref_code") or item.get("引用代号") or "").strip()
            description = (item.get("description") or item.get("形象描述") or "").strip()

            if not name or not ref_code:
                logger.warning(f"跳过无效角色数据: {item}")
                continue

            validated.append({
                "name": name,
                "ref_code": ref_code,
                "description": description,
            })

        return validated if validated else None
```

**代码量对比：**
- 旧版：约 130 行（JSON + Markdown 表格双格式解析）
- 新版：约 75 行（纯 JSON 解析 + 容错提取）

---

### Step 7: 编写单元测试

#### 7.1 ShotParser 测试

**文件：** `tests/test_shot_parser.py`

**测试用例：**
1. ✅ 正常 JSON 格式解析（storyboard + characters）
2. ✅ Markdown 代码块包裹的 JSON 解析
3. ✅ shot_size 枚举值映射测试（6 个有效值）
4. ✅ 未识别的 shot_size 回退到 medium_shot
5. ✅ 缺失字段容错测试
6. ✅ 空 storyboard / characters 数组
7. ✅ 仅 storyboard 无 characters（优化模式）
8. ❌ 无效 JSON 格式抛出 ValueError

#### 7.2 CharacterParser 测试

**文件：** `tests/test_character_parser.py`

**测试用例：**
1. ✅ JSON 数组格式解析
2. ✅ `{"characters": [...]}` 对象格式解析
3. ✅ Markdown 代码块包裹的 JSON 解析
4. ✅ 缺失字段容错测试（name/ref_code 为空则跳过）
5. ❌ 无效格式抛出 ValueError

---

### Step 8: 更新文档

**文件：** `CLAUDE.md`（或等效项目文档）

**添加说明：**
```markdown
### 分镜数据流

1. **LLM 生成** - `TextPromptBuilder.build_storyboard_generation_messages()` 使用 `storyboard_generate.yaml` 模板，要求输出 JSON 格式
2. **解析入库** - `ShotParser.parse()` 解析 JSON，返回 `{"shots": [...], "characters": [...]}`
3. **分镜存储** - `StoryboardService` 将 shots 保存到 storyboard 表
4. **角色存储** - `CharacterService` 将 characters 保存到 character 表

### 角色数据流

1. **LLM 生成** - `TextPromptBuilder.build_character_generation_messages()` 使用 `character_generate.yaml` 模板，输出 JSON 数组
2. **解析入库** - `CharacterParser.parse()` 解析 JSON，返回角色列表
3. **数据库存储** - `CharacterService` 将角色列表保存到 character 表
```

---

## ⚠️ 风险评估

### 风险 1：LLM 不遵守 JSON 格式要求

**概率：** 中
**影响：** 高（解析失败，无法入库）
**缓解措施：**
1. 在提示词中明确强调输出格式，提供完整的 JSON Schema 示例
2. 添加预处理逻辑清洗 Markdown 代码块（` ```json ... ``` `）
3. 记录原始 LLM 响应到日志（`logger.error` 打印前 500 字符）
4. few-shot 示例中使用 JSON 格式输出（`storyboard_generate.yaml` 的 `few_shot_examples` 部分）

### 风险 2：分镜 + 角色合并输出的 JSON 结构过大

**概率：** 低
**影响：** 中（LLM 可能截断或遗漏后半部分）
**缓解措施：**
1. 如果角色表经常被截断，考虑拆分为两次 LLM 调用（先分镜、后角色）
2. 当前 `character_generate.yaml` 已独立存在，拆分后复用即可
3. 短期保持合并输出，监控实际失败率

### 风险 3：色调/光影字段丢失

**概率：** 低
**影响：** 低（Storyboard dataclass 本身没有该字段）
**缓解措施：**
1. 将色调/光影信息合并到 `notes` 字段
2. 提示词中说明：`"notes": "色调：冷蓝调，侧逆光"`

### 风险 4：ShotSize 枚举值不匹配

**概率：** 低
**影响：** 低（使用默认值 `medium_shot`）
**缓解措施：**
1. 在提示词中明确列出所有 6 个枚举值及其中文名称
2. 解析器对未识别值使用默认值 + 日志警告
3. JSON 枚举值与 `ShotSize.value` 一致，避免中文映射歧义

---

## 🔄 回滚方案

如果 JSON 输出方案失败，可回滚到 Markdown 表格格式：

1. **恢复模板文件** — 从 Git 历史恢复 YAML 模板
2. **恢复解析器** — 从 Git 历史恢复 `shot_parser.py`
3. **数据库无需修改** — Storyboard Entity 结构不变

**Git 操作：**
```bash
git log --oneline prompts/templates/storyboard_generate.yaml
git checkout <commit-hash> -- prompts/templates/storyboard_generate.yaml
git checkout <commit-hash> -- prompts/templates/storyboard_optimize.yaml
git checkout <commit-hash> -- utils/shot_parser.py
```

---

## 📊 验证清单

### 分镜生成
- [ ] 模板文件修改完成（`storyboard_generate.yaml`）
- [ ] 模板文件修改完成（`storyboard_optimize.yaml`）
- [ ] 解析器重写完成（`shot_parser.py`）
- [ ] 单元测试通过（`test_shot_parser.py`）
- [ ] 端到端测试通过（剧本 → 分镜生成 → 解析 → 入库 → 显示）
- [ ] 分镜优化端到端测试通过
- [ ] 错误日志记录完善（JSON 解析失败时记录原始响应）

### 角色解析优化
- [ ] 解析器精简完成（`character_parser.py`）
- [ ] 单元测试通过（`test_character_parser.py`）
- [ ] 端到端测试通过（大纲 + 剧本 → 角色生成 → 解析 → 入库 → 显示）

### 集成测试
- [ ] 分镜生成同时输出角色表正常工作
- [ ] Bridge 层入库字段映射正确
- [ ] UI 层正常显示分镜列表和角色列表

---

## 📅 实施步骤

| 步骤 | 内容 | 涉及文件 |
|:---|:---|:---|
| Step 1 | 修改分镜生成 YAML 模板 | `prompts/templates/storyboard_generate.yaml` |
| Step 2 | 修改分镜优化 YAML 模板 | `prompts/templates/storyboard_optimize.yaml` |
| Step 3 | 重写 ShotParser | `utils/shot_parser.py` |
| Step 4 | 更新 TextModelService 调用 | `service/text_model_service.py` |
| Step 5 | 检查 Bridge 层入库逻辑 | `bridge/storyboard_bridge.py` |
| Step 6 | 精简 CharacterParser | `utils/character_parser.py` |
| Step 7 | 编写单元测试 | `tests/test_shot_parser.py`, `tests/test_character_parser.py` |
| Step 8 | 更新文档 | 项目文档 |

---

## 🎯 预期收益

1. **解析成功率** — 从 ~85%（Markdown 表格正则解析）提升到 ~99%（JSON）
2. **代码可维护性** — ShotParser 解析逻辑简化，无需维护列索引映射和中文枚举映射
3. **调试效率** — JSON 格式错误一目了然，调试时间大幅减少
4. **技术一致性** — 与剧本迁移方案（`script_json_migration_plan.md`）保持一致的技术路线
5. **字段对齐** — JSON Schema 字段名与 dataclass 一致，减少转换代码
6. **扩展性** — 未来轻松添加新字段（如角色性格标签、分镜参考图等）

---

**文档版本：** v2.0
**创建日期：** 2026-08-05
**最后更新：** 2026-08-05
**参考文档：** `script_json_migration_plan.md`（已完成的剧本 JSON 迁移方案）
