from loguru import logger

import requests

from config.manager import ConfigManager
from prompts.manager import PromptTemplateManager

class TextModelService:

    DASHSCOPE_TEXT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    DEFAULT_MODEL = "qwen-max"

    def __init__(self, config_manager: ConfigManager, prompt_manager: PromptTemplateManager) -> None:
        self._config = config_manager
        self._prompt_manager = prompt_manager

    def chat(self, messages: list[dict], model: str | None = None) -> str:
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL
        payload = {
            "model": model,
            "input": {"messages": messages},
            "parameters": {"result_format": "message"},
        }
        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"调用文本模型 chat，模型：{model}")
        resp = requests.post(self.DASHSCOPE_TEXT_URL, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        output = data.get("output", {})
        choices = output.get("choices", [])
        if not choices:
            raise RuntimeError("API 未返回有效内容")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("API 返回的内容为空")
        return content

    def optimize_story_outline(
        self,
        original_content: str,
        user_requirement: str,
        model: str | None = None,
    ) -> str:
        template = self._prompt_manager.get_template("outline_optimization")
        messages = template.build_messages(
            original_content=original_content if original_content.strip() else "（空大纲）",
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化大纲，模型：{model or self.DEFAULT_MODEL}")
        return self.chat(messages, model)

    def generate_script(
        self,
        outline_content: str,
        model: str | None = None,
    ) -> tuple[str, list[dict]]:
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL

        system_prompt = """你是一位经验丰富的影视编剧，精通剧本格式规范。请将以下故事内容，按照标准影视剧本格式转换为剧本。

转换规则：

一、场次切分原则
换场规则：只要满足以下任一条件，必须切分新场次：
- 时间变化：从白天到夜晚、从早晨到黄昏、时间跳跃
- 地点变化：从一个房间到另一个房间，从室内到室外
- 时空切换：从现实到回忆/梦境/幻想，或反之

同一场戏内保持：时间连续、地点不变、时空一致。

二、每场戏的格式规范
每场戏包含三个要素，缺一不可：

1. 场景标题
格式：第X场  内景/外景  地点  -  时间
- 场号：从第1场开始连续编号
- 内景/外景：内景（室内）、外景（室外）、内景/外景（内外交界）
- 地点：具体到房间或街区，如"审讯室""老城区街道"
- 时间：日、夜、晨、黄昏、傍晚、凌晨，或具体时刻

2. 动作描述
- 顶格书写，和场景标题之间空一行
- 使用现在时态写谁在做什么、环境如何、情绪氛围
- 只写观众能看到的、听到的，不写心理活动
- 不写摄影机位、景别、运镜

3. 对话/对白
- 角色名：全大写，居中，单独一行
- 对话：角色名下方，自然口语化，一句一行
- 括号说明：如需提示语气或动作，写在角色名下方、对话上方，用括号包住，如（低声）、（停顿）

三、输出格式
- 纯文本，不包含表格、Markdown格式、代码块
- 段落之间空行间隔清晰
- 每场戏写完空两行再接下一场
- 全篇使用中文标点（引号用""）
- 开头写剧名，结尾写"剧终"

直接输出剧本内容，不要添加任何解释或说明。"""

        user_prompt = f"""故事内容：

{outline_content if outline_content.strip() else "（空大纲，请根据常规视频创作流程生成一个简单的剧本示例）"}

请将这份大纲转换为标准影视剧本格式。"""

        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            },
            "parameters": {
                "result_format": "message",
            },
        }

        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"调用文本模型生成剧本，模型：{model}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.DASHSCOPE_TEXT_URL,
                json=payload,
                headers=headers,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")

            output = data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                raise RuntimeError("API 未返回有效内容")

            message = choices[0].get("message", {})
            script_content = message.get("content", "").strip()

            if not script_content:
                raise RuntimeError("API 返回的内容为空")

            logger.info("剧本生成成功")

            from utils.script_parser import ScriptParser

            title, scenes = ScriptParser.parse(script_content)
            logger.info(f"剧本解析成功：标题='{title}'，共 {len(scenes)} 场")

            return title, scenes

        except requests.exceptions.RequestException as e:
            logger.exception("调用文本模型 API 失败")
            raise RuntimeError(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            logger.exception("解析 API 响应失败")
            raise RuntimeError(f"解析响应失败：{e}")

    def generate_storyboard(
        self,
        script_content: str,
        art_style: str = "",
        model: str | None = None,
    ) -> dict:
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL

        system_prompt = """你是一位专业的电影导演兼分镜师。请严格遵循以下步骤与规范，将用户提供的剧本转化为详细的分镜头脚本。

**第一步：确认艺术风格（可选，但推荐）**
请用户指定本次分镜希望采用的艺术风格，例如：韦斯·安德森风格（对称构图、高饱和糖果色）、吉卜力动画风格（手绘质感、自然光影）、赛博朋克风（霓虹光影、雨夜都市）、极简北欧风等。若用户未指定，则采用通用的电影感写实风格。

**第二步：按规则拆分镜头**
仔细阅读剧本，遵循"一处动作变化、情绪转折或场景切换，即拆分一个新镜头"的核心原则。确保剧本的每一句核心剧情都对应一个独立的镜头，避免单个镜头堆砌过多信息。

**重要：场次识别**
剧本中以"第N场"开头的段落标记了不同的场次。你必须准确识别每个镜头所属的场次，并在输出表格的"场次"列中填写对应的场次编号。每个场次的镜头号从1开始重新编号。

**第三步：生成结构化分镜表格**
请使用以下Markdown表格格式输出分镜脚本，表格必须包含以下8个核心要素：

| 场次 | 镜头序号 | 景别 | 画面内容描述 | 运镜方式 | 音效/台词 | 时长(秒) | 色调/光影 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

**各列填写要求：**

1.  **场次**：该镜头所属的场次编号，必须与剧本中"第N场"的编号一致。同一场次的所有镜头应连续排列。
2.  **镜头序号**：每个场次内从1开始按顺序编号，不同场次的镜头号独立编号。
3.  **景别**：必须明确标注为：特写、近景、中景、全景、远景、极近特写等，可附加说明如"面部特写"。
4.  **画面内容描述**：采用"谁+在哪+做什么"的公式。描述需高度具体、可视化，包含人物动作、表情、关键道具、环境细节，并融入用户指定的艺术风格。**禁止使用"伤心"、"激动"等抽象词汇，必须描述可见的细节**（如"垂眸，一滴泪滑过脸颊"）。
5.  **运镜方式**：精准标注，如固定、慢推、拉远、摇镜、跟拍、升降等，并说明其叙事目的（如"慢推以强调情绪"）。
6.  **音效/台词**：标注该镜头内的对白、环境音（如雨声）、特殊音效（如心跳声）或背景音乐提示。
7.  **时长(秒)**：为短剧/短视频设计，单镜头时长建议控制在2-8秒之间。
8.  **色调/光影**：描述镜头的基础色调（如冷蓝调、暖黄调）和关键光影效果（如侧逆光、霓虹灯闪烁），以保持视觉统一。

**第四步：应用创作原则**
- 全片视觉风格需严格统一。
- 每个镜头的描述必须足够具体，确保文生图AI（如Midjourney）或视频生成AI可直接理解并生成画面。

**第五步：输出角色设计表**
在分镜表格之后，请额外输出一张角色设计表，提取剧本和分镜中出现的所有角色。格式如下：

| 角色名 | 引用代号 | 形象描述 |
| :--- | :--- | :--- |

各列要求：
1. **角色名**：角色的中文名字。
2. **引用代号**：使用 CHAR_A、CHAR_B、CHAR_C 等格式，按出场顺序编号。
3. **形象描述**：必须使用以下结构化格式，用方括号标记每个特征分区。分为"固定特征"（跨视频保持一致）和"默认服装"（可根据场景年代/环境替换）两大类：

形象描述格式模板：
[物种] 明确标注角色的种族/物种类型，必须从以下选项中选择一项：人类-白人、人类-黑人、人类-黄种人、人类-其他肤色、动物（注明具体种类如"橘猫"）、拟人化动物（注明具体种类如"拟人化兔子"）、虚拟生物（如"机器人""外星人"）等
[外貌] 年龄+性别+脸型+五官特征，如"25岁女性，瓜子脸，柳叶眉，薄唇"
[发型] 具体发型描述，如"齐肩黑色直发，中分"
[发色] 颜色，如"自然黑"
[瞳色] 颜色，如"深棕色"
[体型] 身高+体型描述，如"165cm，纤细匀称"
[上装] 默认上装描述，如"白色棉质衬衫，袖口卷起"
[裤子] 默认裤子描述，如"深蓝色高腰牛仔裤"
[鞋袜] 默认鞋袜描述，如"白色帆布鞋，无袜"
[帽子] 默认帽子/头饰，如"无"或"灰色贝雷帽"

要求：
- 每个分区必须独立成行，不得合并或省略任何分区
- **物种分区必须放在第一位**，明确标注角色的种族/物种类型，这对AI生成角色外观至关重要
- 固定特征（物种/外貌/发型/发色/瞳色/体型）必须高度具体、可视化，确保视频生成AI在不同镜头中保持角色一致性
- 默认服装描述应匹配剧本中的初始场景，后续分镜中若场景年代/环境变化，服装由分镜画面描述自行提供

直接输出分镜表格和角色设计表，不要添加任何解释或说明。"""

        user_prompt = f"""剧本内容：

{script_content if script_content.strip() else "（空剧本）"}

艺术风格：{art_style if art_style.strip() else "通用电影感写实风格"}

请将这份剧本转换为详细的分镜头脚本（Markdown表格格式）。"""

        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            },
            "parameters": {
                "result_format": "message",
            },
        }

        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"调用文本模型生成分镜，模型：{model}，风格：{art_style or '默认'}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.DASHSCOPE_TEXT_URL,
                json=payload,
                headers=headers,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")

            output = data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                raise RuntimeError("API 未返回有效内容")

            message = choices[0].get("message", {})
            storyboard_content = message.get("content", "").strip()

            if not storyboard_content:
                raise RuntimeError("API 返回的内容为空")

            logger.info("分镜生成成功")

            from utils.shot_parser import ShotParser

            shots = ShotParser.parse(storyboard_content)
            characters = ShotParser.parse_characters(storyboard_content)
            logger.info(f"分镜解析成功：共 {len(shots)} 个镜头，{len(characters)} 个角色")

            return {"shots": shots, "characters": characters}

        except requests.exceptions.RequestException as e:
            logger.exception("调用文本模型 API 失败")
            raise RuntimeError(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            logger.exception("解析 API 响应失败")
            raise RuntimeError(f"解析响应失败：{e}")

    def generate_design_image_prompt(
        self,
        visual_content: str,
        shot_size: str = "",
        camera_movement: str = "",
        dialogue: str = "",
        notes: str = "",
        character_info: str = "",
        model: str | None = None,
    ) -> str:
        template = self._prompt_manager.get_template("image_prompt_generation")
        messages = template.build_messages(
            visual_content=visual_content,
            shot_size=shot_size or "中景",
            camera_movement=camera_movement or "固定",
            dialogue=dialogue or "无",
            notes=notes or "无特殊要求",
            character_info=character_info or "无额外角色信息",
        )

        logger.info(f"调用文本模型生成设计图提示词，模型：{model or self.DEFAULT_MODEL}")
        return self.chat(messages, model)

    def generate_character_design_image_prompt(
        self,
        character_name: str,
        description: str,
        user_requirement: str = "",
        model: str | None = None,
    ) -> str:
        template = self._prompt_manager.get_template("character_image_prompt_generation")
        req_text = f"\n【用户补充要求】\n{user_requirement}" if user_requirement else ""
        messages = template.build_messages(
            character_name=character_name,
            description=description,
            user_requirement=req_text,
        )

        logger.info(f"调用文本模型生成角色设计图提示词，模型：{model or self.DEFAULT_MODEL}，角色：{character_name}")
        return self.chat(messages, model)

    def optimize_screenplay(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
        model: str | None = None
    ) -> tuple[str, list[dict]]:
        """优化剧本：返回 (title, scenes)"""
        template = self._prompt_manager.get_template("screenplay_optimization")
        messages = template.build_messages(
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化剧本，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(messages, model)

        from utils.script_parser import ScriptParser
        title, scenes = ScriptParser.parse(result)
        logger.info(f"剧本解析成功：标题='{title}'，共 {len(scenes)} 场")

        return title, scenes

    def generate_characters(
        self,
        outline_content: str,
        script_content: str,
        user_requirement: str,
        model: str | None = None,
    ) -> list[dict]:
        """生成角色：返回角色列表"""
        template = self._prompt_manager.get_template("character_generation")
        messages = template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型生成角色，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(messages, model)

        from utils.character_parser import CharacterParser
        characters = CharacterParser.parse(result)
        logger.info(f"角色解析成功：共 {len(characters)} 个角色")
        return characters

    def optimize_characters(
        self,
        outline_content: str,
        script_content: str,
        current_characters: str,
        user_requirement: str,
        model: str | None = None,
    ) -> list[dict]:
        """优化角色：返回角色列表"""
        template = self._prompt_manager.get_template("character_optimization")
        messages = template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化角色，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(messages, model)

        from utils.character_parser import CharacterParser
        characters = CharacterParser.parse(result)
        logger.info(f"角色解析成功：共 {len(characters)} 个角色")
        return characters

    def optimize_storyboard(
        self,
        outline_content: str,
        script_content: str,
        character_content: str,
        current_storyboard: str,
        user_requirement: str,
        model: str | None = None,
    ) -> list[dict]:
        """优化分镜：返回分镜列表"""
        template = self._prompt_manager.get_template("storyboard_optimization")
        messages = template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化分镜，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(messages, model)

        from utils.shot_parser import ShotParser
        shots = ShotParser.parse(result)
        logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")
        return shots

    def refine_character_description(
        self,
        character_name: str,
        current_description: str,
        user_requirement: str,
        model: str | None = None,
    ) -> str:
        """根据用户要求修改单个角色的形象描述，返回修改后的描述文本"""
        system_prompt = (
            "你是一个专业的角色形象描述编辑助手。请根据用户的要求，修改角色的形象描述。\n"
            "要求：\n"
            "- 只输出修改后的形象描述文字，不要包含任何解释、标题或额外说明\n"
            "- 保持描述的具体性和可视化程度，适合用于AI图片生成\n"
            "- 如果用户要求不够具体，在合理范围内补充细节"
        )
        user_msg = f"角色名：{character_name}\n当前形象描述：{current_description}\n修改要求：{user_requirement}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        logger.info(f"调用文本模型修改角色描述，角色：{character_name}，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(messages, model)
        return result.strip()
