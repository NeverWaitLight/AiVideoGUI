"""文本模型服务：调用大模型 API 进行文本生成和优化。"""

import logging
from typing import Any

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
