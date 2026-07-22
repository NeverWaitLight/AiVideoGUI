"""文本模型服务：调用大模型 API 进行文本生成和优化。"""

import logging

import requests

from config.manager import ConfigManager

logger = logging.getLogger(__name__)


class TextModelService:
    """文本模型服务：支持调用 DashScope 的通义千问等文本模型。"""

    DASHSCOPE_TEXT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    DEFAULT_MODEL = "qwen-max"  # 通义千问最强模型

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def optimize_outline(
        self,
        original_content: str,
        user_requirement: str,
        model: str | None = None,
    ) -> str:
        """
        使用大模型优化大纲内容。

        Args:
            original_content: 原始大纲内容
            user_requirement: 用户的优化要求
            model: 使用的模型名称，默认使用 qwen-max

        Returns:
            优化后的大纲内容

        Raises:
            RuntimeError: API 调用失败
        """
        # 获取 DashScope 配置
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL

        # 构造优化 prompt
        system_prompt = """你是一个专业的视频项目策划助手。你的任务是根据用户的要求优化视频项目大纲。

要求：
1. 保持大纲的整体结构和核心内容
2. 根据用户的具体要求进行针对性优化
3. 输出的大纲要清晰、有条理
4. 直接输出优化后的大纲内容，不要添加任何解释或说明
"""

        user_prompt = f"""原始大纲：
{original_content if original_content.strip() else "（空大纲）"}

用户的优化要求：
{user_requirement}

请根据用户的要求优化这份大纲，直接输出优化后的大纲内容。"""

        # 调用 DashScope API
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

        logger.info(f"调用文本模型优化大纲，模型：{model}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.DASHSCOPE_TEXT_URL,
                json=payload,
                headers=headers,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")

            # 解析响应
            output = data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                raise RuntimeError("API 未返回有效内容")

            message = choices[0].get("message", {})
            optimized_content = message.get("content", "").strip()

            if not optimized_content:
                raise RuntimeError("API 返回的内容为空")

            logger.info("大纲优化成功")
            return optimized_content

        except requests.exceptions.RequestException as e:
            logger.exception("调用文本模型 API 失败")
            raise RuntimeError(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            logger.exception("解析 API 响应失败")
            raise RuntimeError(f"解析响应失败：{e}")

    def generate_script(
        self,
        outline_content: str,
        model: str | None = None,
    ) -> tuple[str, list[dict]]:
        """
        根据大纲生成剧本内容，并解析为场次结构。

        Args:
            outline_content: 大纲内容
            model: 使用的模型名称，默认使用 qwen-max

        Returns:
            (剧本标题, 场次列表)

        Raises:
            RuntimeError: API 调用失败或解析失败
        """
        # 获取 DashScope 配置
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL

        # 构造剧本生成 prompt（使用专业编剧提示词）
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

        # 调用 DashScope API
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
                timeout=120,  # 剧本生成可能需要更长时间
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")

            # 解析响应
            output = data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                raise RuntimeError("API 未返回有效内容")

            message = choices[0].get("message", {})
            script_content = message.get("content", "").strip()

            if not script_content:
                raise RuntimeError("API 返回的内容为空")

            logger.info("剧本生成成功")

            # 解析剧本为场次结构
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
    ) -> list[dict]:
        """
        根据剧本生成分镜头脚本，并解析为结构化数据。

        Args:
            script_content: 剧本内容
            art_style: 艺术风格（可选，如"韦斯·安德森风格"）
            model: 使用的模型名称，默认使用 qwen-max

        Returns:
            分镜列表（字典格式，待转换为 Shot 对象）

        Raises:
            RuntimeError: API 调用失败或解析失败
        """
        # 获取 DashScope 配置
        provider_config = self._config.get_provider("dashscope")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or self.DEFAULT_MODEL

        # 构造分镜生成 prompt（使用专业导演提示词）
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

直接输出分镜表格，不要添加任何解释或说明。"""

        user_prompt = f"""剧本内容：

{script_content if script_content.strip() else "（空剧本）"}

艺术风格：{art_style if art_style.strip() else "通用电影感写实风格"}

请将这份剧本转换为详细的分镜头脚本（Markdown表格格式）。"""

        # 调用 DashScope API
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

            # 解析响应
            output = data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                raise RuntimeError("API 未返回有效内容")

            message = choices[0].get("message", {})
            storyboard_content = message.get("content", "").strip()

            if not storyboard_content:
                raise RuntimeError("API 返回的内容为空")

            logger.info("分镜生成成功")

            # 解析分镜为结构化数据
            from utils.shot_parser import ShotParser

            shots = ShotParser.parse(storyboard_content)
            logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")

            return shots

        except requests.exceptions.RequestException as e:
            logger.exception("调用文本模型 API 失败")
            raise RuntimeError(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            logger.exception("解析 API 响应失败")
            raise RuntimeError(f"解析响应失败：{e}")
