from loguru import logger

import requests

from config.manager import ConfigManager
from prompts.chat_prompt_builder import ChatPromptBuilder
from utils.ai_request_logger import AIRequestLogger

class ChatModelService:

    DASHSCOPE_TEXT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    DEFAULT_MODEL = "qwen-max"

    def __init__(
        self,
        config_manager: ConfigManager,
        text_prompt_builder: ChatPromptBuilder,
        ai_request_logger: AIRequestLogger | None = None,
    ) -> None:
        self._config = config_manager
        self._prompt_builder = text_prompt_builder
        self._ai_logger = ai_request_logger

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
    ) -> str:
        provider_config = self._config.get_provider_config(name="dashscope", provider_type="chat")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or provider_config.default_model or self.DEFAULT_MODEL
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

        max_retries = 2
        timeout = 1800

        for attempt in range(max_retries):
            try:
                logger.info(f"发起请求（第 {attempt + 1}/{max_retries} 次尝试）")
                resp = requests.post(url=self.DASHSCOPE_TEXT_URL, json=payload, headers=headers, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"请求超时（{timeout}秒），准备重试...")
                    continue
                else:
                    logger.error(f"请求超时（{timeout}秒），已重试 {max_retries} 次，放弃")
                    raise RuntimeError(f"文本生成请求超时（{timeout}秒），请检查网络连接或稍后重试")
            except requests.exceptions.RequestException as e:
                logger.exception("文本生成请求失败")
                raise RuntimeError(f"网络请求失败：{e}")

        if self._ai_logger:
            self._ai_logger.log_request(
                request_type="text_generation",
                module=module,
                payload={"url": self.DASHSCOPE_TEXT_URL, "json": payload, "headers": headers},
                response=data,
                project_id=project_id,
                project_name=project_name,
                context=context or "文本生成",
            )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        messages = self._prompt_builder.build_outline_optimization_messages(
            original_content=original_content,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化大纲，模型：{model or self.DEFAULT_MODEL}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="outline",
            context="大纲优化",
        )

    def generate_script(
        self,
        outline_content: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict]]:
        provider_config = self._config.get_provider_config(name="dashscope", provider_type="chat")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or provider_config.default_model or self.DEFAULT_MODEL

        messages = self._prompt_builder.build_script_generation_messages(outline_content)

        payload = {
            "model": model,
            "input": {"messages": messages},
            "parameters": {
                "result_format": "message",
                "max_tokens": 16384,
            },
        }

        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"调用文本模型生成剧本，模型：{model}")
        logger.debug(f"请求体：{payload}")

        max_retries = 2
        timeout = 1800

        try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"发起请求（第 {attempt + 1}/{max_retries} 次尝试）")
                    resp = requests.post(
                        self.DASHSCOPE_TEXT_URL,
                        json=payload,
                        headers=headers,
                        timeout=timeout,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    logger.debug(f"响应：{data}")
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        logger.warning(f"请求超时（{timeout}秒），准备重试...")
                        continue
                    else:
                        logger.error(f"请求超时（{timeout}秒），已重试 {max_retries} 次，放弃")
                        raise RuntimeError(f"剧本生成请求超时（{timeout}秒），请检查网络连接或稍后重试")

            if self._ai_logger:
                self._ai_logger.log_request(
                    request_type="text_generation",
                    module="script",
                    payload={"url": self.DASHSCOPE_TEXT_URL, "json": payload, "headers": headers},
                    response=data,
                    project_id=project_id,
                    project_name=project_name,
                    context="剧本生成",
                )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> list[dict]:
        provider_config = self._config.get_provider_config(name="dashscope", provider_type="chat")
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置 DashScope API Key，请在设置中配置")

        model = model or provider_config.default_model or self.DEFAULT_MODEL

        messages = self._prompt_builder.build_storyboard_generation_messages(
            script_content=script_content,
            art_style=art_style,
        )

        payload = {
            "model": model,
            "input": {"messages": messages},
            "parameters": {
                "result_format": "message",
                "max_tokens": 16384,
            },
        }

        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"调用文本模型生成分镜，模型：{model}，风格：{art_style or '默认'}")
        logger.debug(f"请求体：{payload}")

        max_retries = 2
        timeout = 1800

        try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"发起请求（第 {attempt + 1}/{max_retries} 次尝试）")
                    resp = requests.post(
                        self.DASHSCOPE_TEXT_URL,
                        json=payload,
                        headers=headers,
                        timeout=timeout,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    logger.debug(f"响应：{data}")
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        logger.warning(f"请求超时（{timeout}秒），准备重试...")
                        continue
                    else:
                        logger.error(f"请求超时（{timeout}秒），已重试 {max_retries} 次，放弃")
                        raise RuntimeError(f"分镜生成请求超时（{timeout}秒），请检查网络连接或稍后重试")

            if self._ai_logger:
                self._ai_logger.log_request(
                    request_type="text_generation",
                    module="storyboard",
                    payload={"url": self.DASHSCOPE_TEXT_URL, "json": payload, "headers": headers},
                    response=data,
                    project_id=project_id,
                    project_name=project_name,
                    context="分镜生成",
                )

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
            logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")

            return shots

        except requests.exceptions.RequestException as e:
            logger.exception("调用文本模型 API 失败")
            raise RuntimeError(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            logger.exception("解析 API 响应失败")
            raise RuntimeError(f"解析响应失败：{e}")

    def generate_design_image_prompt(
        self,
        content: str,
        shot_size: str = "",
        camera_movement: str = "",
        notes: str = "",
        character_info: str = "",
        visual_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        messages = self._prompt_builder.build_design_image_prompt_messages(
            content=content,
            shot_size=shot_size,
            camera_movement=camera_movement,
            notes=notes,
            character_info=character_info,
            visual_style=visual_style,
        )

        logger.info(f"调用文本模型生成设计图提示词，模型：{model or self.DEFAULT_MODEL}，风格：{visual_style or '默认'}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜设计图提示词生成",
        )

    def generate_character_design_image_prompt(
        self,
        character_name: str,
        description: str,
        user_requirement: str = "",
        visual_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        messages = self._prompt_builder.build_character_design_image_prompt_messages(
            character_name=character_name,
            description=description,
            user_requirement=user_requirement,
            visual_style=visual_style,
        )

        logger.info(f"调用文本模型生成角色设计图提示词，模型：{model or self.DEFAULT_MODEL}，角色：{character_name}，风格：{visual_style or '默认'}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context=f"角色设计图提示词生成 - {character_name}",
        )

    def optimize_screenplay(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict]]:
        """优化剧本：返回 (title, scenes)"""
        messages = self._prompt_builder.build_screenplay_optimization_messages(
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化剧本，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本优化",
        )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> list[dict]:
        """生成角色：返回角色列表"""
        messages = self._prompt_builder.build_character_generation_messages(
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型生成角色，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色生成",
        )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> list[dict]:
        """优化角色：返回角色列表"""
        messages = self._prompt_builder.build_character_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化角色，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色优化",
        )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> list[dict]:
        """优化分镜：返回分镜列表"""
        messages = self._prompt_builder.build_storyboard_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化分镜，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜优化",
        )

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
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        """根据用户要求修改单个角色的形象描述，返回修改后的描述文本"""
        messages = self._prompt_builder.build_character_description_refine_messages(
            character_name=character_name,
            current_description=current_description,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型修改角色描述，角色：{character_name}，模型：{model or self.DEFAULT_MODEL}")
        result = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context=f"角色描述优化 - {character_name}",
        )
        return result.strip()

    def generate_cover_image_prompt(
        self,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_info: str,
        visual_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
    ) -> str:
        """生成项目封面图提示词"""
        messages = self._prompt_builder.build_cover_image_prompt_messages(
            project_name=project_name,
            aspect_ratio=aspect_ratio,
            outline_content=outline_content,
            character_info=character_info,
            visual_style=visual_style,
        )

        logger.info(f"调用文本模型生成封面图提示词，项目：{project_name}，模型：{model or self.DEFAULT_MODEL}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="cover",
            context="项目封面图提示词生成",
        )
