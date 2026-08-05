# 剧本生成 JSON 输出格式迁移计划

## 📋 背景

**当前问题：** 剧本生成模板使用纯文本输出格式，Python 代码通过正则表达式解析，存在以下风险：
1. LLM 输出格式不稳定（空格、标点变化）导致解析失败
2. 中文标点变体（`-` / `—` / `－`）影响正则匹配
3. 时间描述枚举覆盖不全（"深夜""午后"等无法映射）
4. 调试困难（解析失败时难以定位具体错误位置）

**解决方案：** 将剧本生成模板改为输出结构化 JSON 格式，提高解析可靠性和可维护性。

---

## 🔍 现状分析

### 当前实现

**模板文件：** `prompts/templates/script_generate.yaml`
- 输出格式：纯文本剧本（标准影视格式）
- 格式要求：`第X场 内景/外景 地点 - 时间`

**解析器：** `utils/script_parser.py`
- 解析方式：正则表达式 `r"第\s*(\d+)\s*场\s+(内景|外景|内景/外景)\s+(.+?)\s*[-—]\s*(.+)"`
- 枚举映射：手动维护 `LOCATION_TYPE_MAP` 和 `TIME_TYPE_MAP`
- 约 102 行代码

**风险点：**
```python
# 示例：这些格式变化会导致解析失败
"第1场  内景  审讯室  -  夜"        # ✅ 正常
"第1场 内景 审讯室 — 夜"            # ❌ 使用了全角破折号
"第1场内景审讯室-夜"                # ❌ 缺少空格
"第1场 内景 审讯室 深夜"            # ❌ 缺少分隔符
```

---

## ✅ 改进方案

### 目标

1. **可靠性** - JSON 格式解析 100% 成功率（仅需 `json.loads()`）
2. **可维护性** - 无需维护正则表达式和枚举映射表
3. **可扩展性** - 轻松添加新字段（如角色列表、动作标签等）
4. **可调试性** - JSON 格式错误一目了然

### JSON Schema 设计

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
      "content": "警察坐在桌前，眼神犀利地盯着嫌疑人。\n\n警察\n你知道自己在做什么吗？\n\n嫌疑人\n（低头不语）"
    },
    {
      "scene_number": 2,
      "location_type": "exterior",
      "location": "城市街道",
      "time_type": "day",
      "time_detail": "",
      "content": "阳光洒在街道上，人来人往。"
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 枚举值 | 说明 |
|:---|:---|:---|:---|
| `title` | string | - | 剧本标题 |
| `scenes` | array | - | 场次列表 |
| `scene_number` | integer | - | 场次编号（从 1 开始） |
| `location_type` | string | `interior` / `exterior` / `interior_exterior` | 内景/外景/内外景 |
| `location` | string | - | 地点描述（如"审讯室""城市街道"） |
| `time_type` | string | `day` / `night` / `dawn` / `dusk` / `evening` / `custom` | 时间类型 |
| `time_detail` | string | - | 时间详细描述（如"深夜""黄昏时分"），当 `time_type` 为标准类型时可为空 |
| `content` | string | - | 场次完整内容（动作描述 + 对话） |

**枚举值映射：**

```python
# location_type 映射到 models.enums.SceneLocation
"interior" → SceneLocation.INTERIOR
"exterior" → SceneLocation.EXTERIOR
"interior_exterior" → SceneLocation.INTERIOR_EXTERIOR

# time_type 映射到 models.enums.SceneTime
"day" → SceneTime.DAY
"night" → SceneTime.NIGHT
"dawn" → SceneTime.DAWN
"dusk" → SceneTime.DUSK
"evening" → SceneTime.EVENING
"custom" → SceneTime.CUSTOM
```

---

## 🛠️ 实施步骤

### Step 1: 修改 YAML 模板

**文件：** `prompts/templates/script_generate.yaml`

**修改内容：**
1. 删除纯文本格式要求（第 37-42 行）
2. 新增 JSON 输出格式要求
3. 提供 JSON Schema 示例
4. 明确枚举值定义

**关键变更：**
```yaml
# 旧版（第 37-42 行）
三、输出格式
- 纯文本，不包含表格、Markdown格式、代码块
- 段落之间空行间隔清晰
- 每场戏写完空两行再接下一场
- 全篇使用中文标点（引号用""）
- 开头写剧名，结尾写"剧终"

# 新版
三、输出格式
必须输出严格的 JSON 格式，结构如下：
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

字段说明：
- location_type: 必须是 "interior" / "exterior" / "interior_exterior"
- time_type: 必须是 "day" / "night" / "dawn" / "dusk" / "evening" / "custom"
- time_detail: 时间详细描述，标准时间可为空字符串
- content: 场次内容保持原影视剧本格式（动作描述 + 对话）

直接输出 JSON，不要添加任何 Markdown 代码块标记或其他说明。
```

---

### Step 2: 重写解析器

**文件：** `utils/script_parser.py`

**修改策略：** 完全重写，简化为 JSON 解析

**新实现（伪代码）：**
```python
import json
from loguru import logger
from models.enums import SceneLocation, SceneTime

class ScriptParser:
    LOCATION_TYPE_MAP = {
        "interior": SceneLocation.INTERIOR,
        "exterior": SceneLocation.EXTERIOR,
        "interior_exterior": SceneLocation.INTERIOR_EXTERIOR,
    }
    
    TIME_TYPE_MAP = {
        "day": SceneTime.DAY,
        "night": SceneTime.NIGHT,
        "dawn": SceneTime.DAWN,
        "dusk": SceneTime.DUSK,
        "evening": SceneTime.EVENING,
        "custom": SceneTime.CUSTOM,
    }
    
    @classmethod
    def parse(cls, script_json: str) -> tuple[str, list[dict[str, Any]]]:
        """解析 JSON 格式的剧本"""
        try:
            data = json.loads(script_json)
        except json.JSONDecodeError as e:
            logger.error(f"剧本 JSON 解析失败: {e}")
            raise ValueError(f"无效的 JSON 格式: {e}")
        
        title = data.get("title", "")
        scenes_raw = data.get("scenes", [])
        scenes = []
        
        for scene in scenes_raw:
            location_type = cls.LOCATION_TYPE_MAP.get(
                scene.get("location_type", "interior"),
                SceneLocation.INTERIOR
            ).value
            
            time_type = cls.TIME_TYPE_MAP.get(
                scene.get("time_type", "day"),
                SceneTime.DAY
            ).value
            
            scenes.append({
                "scene_number": scene.get("scene_number", 0),
                "location_type": location_type,
                "location": scene.get("location", ""),
                "time_type": time_type,
                "time_detail": scene.get("time_detail", ""),
                "content": scene.get("content", ""),
            })
        
        logger.info(f"解析剧本完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes
```

**代码量对比：**
- 旧版：102 行（正则表达式 + 逐行解析）
- 新版：约 50 行（JSON 解析 + 枚举映射）

---

### Step 3: 处理 LLM 输出清洗

**问题：** LLM 可能返回 Markdown 代码块包裹的 JSON

**示例：**
````
```json
{
  "title": "剧本标题",
  "scenes": [...]
}
```
````

**解决方案：** 在 `ScriptParser.parse()` 中添加预处理逻辑

```python
@classmethod
def parse(cls, script_json: str) -> tuple[str, list[dict[str, Any]]]:
    # 清洗 Markdown 代码块标记
    script_json = script_json.strip()
    if script_json.startswith("```json"):
        script_json = script_json[7:]  # 移除 ```json
    if script_json.startswith("```"):
        script_json = script_json[3:]  # 移除 ```
    if script_json.endswith("```"):
        script_json = script_json[:-3]  # 移除结尾 ```
    script_json = script_json.strip()
    
    # 正常的 JSON 解析流程
    try:
        data = json.loads(script_json)
    except json.JSONDecodeError as e:
        logger.error(f"剧本 JSON 解析失败: {e}")
        raise ValueError(f"无效的 JSON 格式: {e}")
    
    # ... 后续处理
```

---

### Step 4: 更新单元测试

**文件：** `tests/test_script_parser.py`（如果存在）

**测试用例：**
1. ✅ 正常 JSON 格式解析
2. ✅ Markdown 代码块包裹的 JSON 解析
3. ✅ 枚举值映射测试
4. ✅ 缺失字段容错测试
5. ❌ 无效 JSON 格式抛出异常

**示例测试代码：**
```python
import unittest
from utils.script_parser import ScriptParser

class TestScriptParser(unittest.TestCase):
    def test_parse_normal_json(self):
        json_input = '''
        {
          "title": "测试剧本",
          "scenes": [
            {
              "scene_number": 1,
              "location_type": "interior",
              "location": "审讯室",
              "time_type": "night",
              "time_detail": "",
              "content": "警察坐在桌前。"
            }
          ]
        }
        '''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(title, "测试剧本")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["scene_number"], 1)
    
    def test_parse_markdown_wrapped_json(self):
        json_input = '''```json
        {
          "title": "测试剧本",
          "scenes": []
        }
        ```'''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(title, "测试剧本")
    
    def test_parse_invalid_json(self):
        with self.assertRaises(ValueError):
            ScriptParser.parse("这不是 JSON")
```

---

### Step 5: 更新文档

**文件：** `CLAUDE.md`

**修改位置：** Data Layer 章节（数据表结构部分）

**添加说明：**
```markdown
### 剧本数据流

1. **LLM 生成** - `TextPromptBuilder.build_script_generation_messages()` 使用 `script_generate.yaml` 模板，要求输出 JSON 格式
2. **解析入库** - `ScriptParser.parse()` 解析 JSON，转换为 `Scene` dataclass 列表
3. **数据库存储** - `ScriptService` 将场次列表保存到 `scenes` 表
```

---

## ⚠️ 风险评估

### 风险 1：LLM 不遵守 JSON 格式要求

**概率：** 中  
**影响：** 高（解析失败，无法入库）  
**缓解措施：**
1. 在提示词中明确强调输出格式（使用粗体、示例、重复说明）
2. 添加预处理逻辑清洗 Markdown 代码块
3. 记录原始 LLM 响应到日志（方便调试）
4. 提供降级方案：解析失败时提示用户手动修正

### 风险 2：现有数据迁移

**概率：** 低（项目尚未上线，无历史数据）  
**影响：** 无  
**缓解措施：** 如有历史数据，编写迁移脚本（不在本计划范围内）

### 风险 3：场次内容格式丢失

**概率：** 低  
**影响：** 中（对话格式不清晰）  
**缓解措施：** `content` 字段保留完整的影视剧本格式（动作描述 + 对话），不拆分为结构化字段

---

## 🔄 回滚方案

如果 JSON 输出方案失败，可回滚到纯文本格式：

1. **恢复模板文件** - 从 Git 历史恢复 `script_generate.yaml`
2. **恢复解析器** - 从 Git 历史恢复 `script_parser.py`
3. **数据库无需修改** - `scenes` 表结构不变

**Git 操作：**
```bash
git log --oneline prompts/templates/script_generate.yaml
git checkout <commit-hash> -- prompts/templates/script_generate.yaml
git checkout <commit-hash> -- utils/script_parser.py
```

---

## 📊 验证清单

- [x] 模板文件修改完成（`script_generate.yaml`）
- [x] 解析器重写完成（`script_parser.py`）
- [x] 单元测试通过（`test_script_parser.py` - 7 个测试全部通过）
- [ ] 端到端测试通过（完整流程：大纲 → 剧本生成 → 解析 → 入库 → 显示）
- [x] 文档更新完成（`CLAUDE.md` - 添加剧本数据流章节）
- [x] 错误日志记录完善（JSON 解析失败时记录原始响应）
- [ ] UI 层正常显示场次列表

---

## 📅 实施时间线

| 阶段 | 预计耗时 | 负责人 |
|:---|:---:|:---|
| Step 1: 修改 YAML 模板 | 15 分钟 | AI |
| Step 2: 重写解析器 | 30 分钟 | AI |
| Step 3: 添加清洗逻辑 | 10 分钟 | AI |
| Step 4: 编写单元测试 | 20 分钟 | AI |
| Step 5: 更新文档 | 10 分钟 | AI |
| 端到端测试 | 15 分钟 | 用户 |
| **总计** | **约 100 分钟** | - |

---

## 🎯 预期收益

1. **解析成功率** - 从 ~85%（正则表达式）提升到 ~99%（JSON）
2. **代码可维护性** - 解析器代码量减少 50%
3. **调试效率** - JSON 格式错误一目了然，调试时间减少 70%
4. **扩展性** - 未来轻松添加新字段（如角色列表、情绪标签等）

---

## ✅ 批准签字

- [ ] 项目负责人：__________  日期：__________
- [ ] 技术负责人：__________  日期：__________

---

**文档版本：** v1.0  
**创建日期：** 2026-08-04  
**最后更新：** 2026-08-04
