from loguru import logger

import os
import litellm

from config.manager import ConfigManager
from prompts.chat_prompt_builder import ChatPromptBuilder
from utils.ai_request_logger import AIRequestLogger

class ChatModelService:

    def __init__(
        self,
        config_manager: ConfigManager,
        text_prompt_builder: ChatPromptBuilder,
        ai_request_logger: AIRequestLogger | None = None,
    ) -> None:
        self._config = config_manager
        self._prompt_builder = text_prompt_builder
        self._ai_logger = ai_request_logger

        # 设置 litellm 环境变量（禁用远程定价获取和自动忽略不支持的参数）
        os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
        os.environ["LITELLM_DROP_PARAMS"] = "True"

    def _setup_litellm_env(self, provider_id: str) -> tuple[str, dict]:
        """
        设置 litellm 所需的环境变量，返回 (model_name, litellm_params)

        Args:
            provider_id: 厂商 ID

        Returns:
            (model_name, litellm_params): 模型名称和 litellm 额外参数

        Raises:
            RuntimeError: 配置错误或缺失
        """
        preset = self._config.get_chat_provider_preset(provider_id)
        if not preset:
            raise RuntimeError(f"未找到聊天模型厂商预设：{provider_id}")

        credential = self._config.get_chat_provider_credential(provider_id)
        if not credential:
            raise RuntimeError(f"未配置聊天模型厂商凭证：{provider_id}，请在设置中配置")

        litellm_params = {}

        if preset.type == "custom":
            # 自定义 OpenAI 协议
            if not credential.api_key:
                raise RuntimeError(f"未配置 {preset.display_name} 的 API Key，请在设置中配置")
            if not credential.base_url:
                raise RuntimeError(f"未配置 {preset.display_name} 的 Base URL，请在设置中配置")
            if not credential.model:
                raise RuntimeError(f"未配置 {preset.display_name} 的 Model，请在设置中配置")

            os.environ["OPENAI_API_KEY"] = credential.api_key
            litellm_params["api_base"] = credential.base_url
            model_name = credential.model

        else:
            # 预设厂商
            if not credential.api_key:
                raise RuntimeError(f"未配置 {preset.display_name} 的 API Key，请在设置中配置")

            # 设置环境变量
            os.environ[preset.api_key_env] = credential.api_key

            # 使用预设的默认模型
            model_name = f"{preset.model_prefix}{preset.default_model}"

        return model_name, litellm_params

    def _call_litellm(
        self,
        messages: list[dict],
        model_override: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "chat",
        context: str | None = None,
    ) -> str:
        """
        调用 litellm 完成文本生成

        Args:
            messages: 消息列表
            model_override: 覆盖默认模型（可选）
            project_id: 项目 ID（用于日志）
            project_name: 项目名称（用于日志）
            module: 模块名称（用于日志）
            context: 上下文描述（用于日志）

        Returns:
            生成的文本内容

        Raises:
            RuntimeError: API 调用失败
        """
        provider_id = self._config.get_active_chat_provider_id()
        if not provider_id:
            raise RuntimeError("未选择聊天模型厂商，请在设置中配置")

        model_name, litellm_params = self._setup_litellm_env(provider_id)

        # 如果有覆盖模型，使用覆盖模型（保留 prefix）
        if model_override:
            preset = self._config.get_chat_provider_preset(provider_id)
            if preset and preset.model_prefix:
                if not model_override.startswith(preset.model_prefix):
                    model_name = f"{preset.model_prefix}{model_override}"
                else:
                    model_name = model_override
            else:
                model_name = model_override

        logger.info(f"调用 litellm 文本生成，模型：{model_name}")

        max_retries = 2
        timeout = 1800

        for attempt in range(max_retries):
            try:
                logger.info(f"发起请求（第 {attempt + 1}/{max_retries} 次尝试）")

                response = litellm.completion(
                    model=model_name,
                    messages=messages,
                    timeout=timeout,
                    **litellm_params,
                )

                if self._ai_logger:
                    self._ai_logger.log_request(
                        request_type="text_generation",
                        module=module,
                        payload={"model": model_name, "messages": messages, "litellm_params": litellm_params},
                        response=response.model_dump() if hasattr(response, "model_dump") else str(response),
                        project_id=project_id,
                        project_name=project_name,
                        context=context or "文本生成",
                    )

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise RuntimeError("API 返回的内容为空")

                return content.strip()

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"请求失败，准备重试：{e}")
                    continue
                else:
                    logger.exception("文本生成请求失败")
                    raise RuntimeError(f"文本生成失败：{e}")

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
    ) -> str:
        return self._call_litellm(
            messages=messages,
            model_override=model,
            project_id=project_id,
            project_name=project_name,
            module=module,
            context=context,
        )

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

        logger.info(f"调用文本模型优化大纲")
        return self._call_litellm(
            messages=messages,
            model_override=model,
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
        messages = self._prompt_builder.build_script_generation_messages(outline_content)

        logger.info(f"调用文本模型生成剧本")

        script_content = self._call_litellm(
            messages=messages,
            model_override=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本生成",
        )

        from utils.script_parser import ScriptParser

        title, scenes = ScriptParser.parse(script_content)
        logger.info(f"剧本解析成功：标题='{title}'，共 {len(scenes)} 场")

        return title, scenes

    def generate_storyboard(
        self,
        script_content: str,
        art_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> list[dict]:
        messages = self._prompt_builder.build_storyboard_generation_messages(
            script_content=script_content,
            art_style=art_style,
        )

        logger.info(f"调用文本模型生成分镜，风格：{art_style or '默认'}")

        storyboard_content = self._call_litellm(
            messages=messages,
            model_override=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜生成",
        )

        from utils.shot_parser import ShotParser

        shots = ShotParser.parse(storyboard_content)
        logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")

        return shots

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

        logger.info(f"调用文本模型生成设计图提示词，风格：{visual_style or '默认'}")
        return self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型生成角色设计图提示词，角色：{character_name}，风格：{visual_style or '默认'}")
        return self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型优化剧本")
        result = self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型生成角色")
        result = self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型优化角色")
        result = self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型优化分镜")
        result = self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型修改角色描述，角色：{character_name}")
        result = self._call_litellm(
            messages=messages,
            model_override=model,
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

        logger.info(f"调用文本模型生成封面图提示词，项目：{project_name}")
        return self._call_litellm(
            messages=messages,
            model_override=model,
            project_id=project_id,
            project_name=project_name,
            module="cover",
            context="项目封面图提示词生成",
        )
