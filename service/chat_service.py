from loguru import logger

from collections.abc import Callable

from config.manager import ConfigManager
from models.enums import GenerateTaskCallerType
from models.generate_task_context import GenerateTaskContext
from prompts.chat_prompt_builder import ChatPromptBuilder
from providers.anyllm_chat import AnyLLMChatProvider
from providers.chat_base import ChatProvider
from providers.generate_task_recorder import GenerateTaskRecorder
from storage.session_manager import SessionManager
from utils.prompt_sanitize import sanitize_chat_messages

_PROVIDER_REGISTRY: dict[str, type[ChatProvider]] = {
    "dashscope": AnyLLMChatProvider,
    "deepseek": AnyLLMChatProvider,
    "openai": AnyLLMChatProvider,
}


class ChatService:

    DEFAULT_MODEL = "qwen3.5-plus"
    _MAX_RETRIES = 2
    _TIMEOUT_SECONDS = 1800

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        text_prompt_builder: ChatPromptBuilder,
    ) -> None:
        self._config = config_manager
        self._sm = session_manager
        self._prompt_builder = text_prompt_builder
        self._providers: dict[str, ChatProvider] = {}

    def invalidate_provider_cache(self) -> None:
        if self._providers:
            logger.info("清空 Provider 缓存：chat")
        self._providers.clear()

    def _get_provider_config(self):
        provider_name = self._config.settings.default_chat_provider or "dashscope"
        provider_config = self._config.resolve_config_for_type(
            name=provider_name,
            provider_type="chat",
        )
        if not provider_config or not provider_config.api_key:
            raise RuntimeError("未配置文本模型 API Key，请在设置中配置")
        return provider_name, provider_config

    def _get_provider(self) -> ChatProvider:
        provider_name, provider_config = self._get_provider_config()

        if provider_name not in _PROVIDER_REGISTRY:
            logger.warning(f"未知的文本模型供应商 {provider_name}，回退到 dashscope")
            provider_name = "dashscope"
            provider_config = self._config.resolve_config_for_type(
                name=provider_name,
                provider_type="chat",
            )
            if not provider_config or not provider_config.api_key:
                raise RuntimeError("未配置文本模型 API Key，请在设置中配置")

        if provider_name in self._providers:
            return self._providers[provider_name]

        cls = _PROVIDER_REGISTRY[provider_name]
        provider = cls(provider_config)
        self._providers[provider_name] = provider
        logger.info(f"初始化文本模型 Provider：{provider_name}")
        return provider

    def _resolve_model(self, model: str | None) -> str:
        provider = self._get_provider()
        if model:
            return provider._resolve_model(model)
        _, provider_config = self._get_provider_config()
        return provider._resolve_model(provider_config.default_model or None)

    def _is_timeout_error(self, error: Exception) -> bool:
        message = str(error).lower()
        return "timeout" in message or "超时" in message

    def _call_provider(
        self,
        messages: list[dict],
        model: str,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
        **provider_kwargs,
    ) -> tuple[str, int | None]:
        provider = self._get_provider()
        last_error: Exception | None = None

        sanitized_messages = sanitize_chat_messages(messages)
        task_context = GenerateTaskContext(
            session_manager=self._sm,
            parent_ids=parent_ids,
            caller_type=caller_type,
            caller_id=caller_id,
            project_id=project_id,
            project_name=project_name,
            module=module,
            context=context,
        )

        for attempt in range(self._MAX_RETRIES):
            try:
                logger.info(f"发起请求（第 {attempt + 1}/{self._MAX_RETRIES} 次尝试）")
                content, task_id = provider.chat(
                    messages=sanitized_messages,
                    model=model,
                    task_context=task_context,
                    **provider_kwargs,
                )
                if not content:
                    raise RuntimeError("API 返回的内容为空")
                return content, task_id
            except RuntimeError as e:
                last_error = e
                if self._is_timeout_error(e) and attempt < self._MAX_RETRIES - 1:
                    logger.warning(f"请求超时（{self._TIMEOUT_SECONDS}秒），准备重试...")
                    continue
                raise
            except Exception as e:
                logger.exception("文本生成请求失败")
                raise RuntimeError(f"文本模型调用失败：{e}") from e

        if last_error:
            if self._is_timeout_error(last_error):
                raise RuntimeError(
                    f"文本生成请求超时（{self._TIMEOUT_SECONDS}秒），请检查网络连接或稍后重试"
                ) from last_error
            raise last_error
        raise RuntimeError("文本模型调用失败")

    def _call_provider_stream(
        self,
        messages: list[dict],
        on_chunk: Callable[[str], None] | None,
        model: str,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
        **provider_kwargs,
    ) -> tuple[str, int | None]:
        provider = self._get_provider()
        last_error: Exception | None = None

        sanitized_messages = sanitize_chat_messages(messages)
        task_context = GenerateTaskContext(
            session_manager=self._sm,
            parent_ids=parent_ids,
            caller_type=caller_type,
            caller_id=caller_id,
            project_id=project_id,
            project_name=project_name,
            module=module,
            context=context,
        )

        for attempt in range(self._MAX_RETRIES):
            try:
                logger.info(f"发起流式请求（第 {attempt + 1}/{self._MAX_RETRIES} 次尝试）")
                content, task_id = provider.chat_stream(
                    messages=sanitized_messages,
                    model=model,
                    task_context=task_context,
                    on_chunk=on_chunk,
                    **provider_kwargs,
                )
                if not content:
                    raise RuntimeError("API 返回的内容为空")
                return content, task_id
            except RuntimeError as e:
                last_error = e
                if self._is_timeout_error(e) and attempt < self._MAX_RETRIES - 1:
                    logger.warning(f"请求超时（{self._TIMEOUT_SECONDS}秒），准备重试...")
                    continue
                raise
            except Exception as e:
                logger.exception("文本流式生成请求失败")
                raise RuntimeError(f"文本模型调用失败：{e}") from e

        if last_error:
            if self._is_timeout_error(last_error):
                raise RuntimeError(
                    f"文本生成请求超时（{self._TIMEOUT_SECONDS}秒），请检查网络连接或稍后重试"
                ) from last_error
            raise last_error
        raise RuntimeError("文本模型调用失败")

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
        **provider_kwargs,
    ) -> tuple[str, int]:
        model = self._resolve_model(model)
        logger.info(f"调用文本模型 chat，模型：{model}")

        content, task_id = self._call_provider(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module=module,
            context=context,
            caller_type=caller_type,
            caller_id=caller_id,
            parent_ids=parent_ids,
            **provider_kwargs,
        )
        if task_id is None:
            raise RuntimeError("文本模型任务创建失败")
        return content, task_id

    def optimize_story_outline(
        self,
        original_content: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_outline_optimization_messages(
            original_content=original_content,
            user_requirement=user_requirement,
        )

        resolved_model = self._resolve_model(model)
        logger.info(f"调用文本模型优化大纲（流式），模型：{resolved_model}")
        content, task_id = self._call_provider_stream(
            messages=messages,
            on_chunk=on_chunk,
            model=resolved_model,
            project_id=project_id,
            project_name=project_name,
            module="outline",
            context="大纲优化",
            caller_type=GenerateTaskCallerType.OUTLINE,
            caller_id=str(project_id) if project_id else "",
        )
        if task_id is None:
            raise RuntimeError("文本模型任务创建失败")
        return content, task_id

    def generate_script(
        self,
        outline_content: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict], int]:
        messages = self._prompt_builder.build_script_generation_messages(outline_content)

        resolved_model = self._resolve_model(model)
        logger.info(f"调用文本模型生成剧本，模型：{resolved_model}")
        script_content, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本生成",
            caller_type=GenerateTaskCallerType.SCRIPT,
            caller_id=str(project_id) if project_id else "",
            max_tokens=16384,
        )

        logger.info("剧本生成成功")

        from utils.script_parser import ScriptParser

        try:
            title, scenes = ScriptParser.parse(script_content)
        except ValueError as e:
            GenerateTaskRecorder(self._sm).mark_failed(task_id, f"解析响应失败：{e}")
            raise RuntimeError(f"解析响应失败：{e}") from e

        logger.info(f"剧本解析成功：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes, task_id

    def _stream_and_parse_items(
        self,
        *,
        messages: list[dict],
        array_key: str,
        parse_item: Callable[[dict], dict],
        parse_full: Callable[[str], tuple],
        on_item: Callable[[dict], None] | None,
        model: str | None,
        project_id: int | None,
        project_name: str | None,
        module: str,
        context: str,
        caller_type: GenerateTaskCallerType,
        max_tokens: int = 16384,
    ):
        from utils.streaming_json_array_parser import StreamingJsonArrayParser

        resolved_model = self._resolve_model(model)
        parser = StreamingJsonArrayParser(array_key=array_key)

        def _on_chunk(delta: str) -> None:
            for raw_item in parser.feed(delta):
                parsed = parse_item(raw_item)
                if parsed is None:
                    continue
                if on_item:
                    on_item(parsed)

        content, task_id = self._call_provider_stream(
            messages=messages,
            on_chunk=_on_chunk,
            model=resolved_model,
            project_id=project_id,
            project_name=project_name,
            module=module,
            context=context,
            caller_type=caller_type,
            caller_id=str(project_id) if project_id else "",
            max_tokens=max_tokens,
        )
        if task_id is None:
            raise RuntimeError("文本模型任务创建失败")

        try:
            return parse_full(content), task_id
        except ValueError as e:
            GenerateTaskRecorder(self._sm).mark_failed(task_id, f"解析响应失败：{e}")
            raise RuntimeError(f"解析响应失败：{e}") from e

    def generate_script_stream(
        self,
        outline_content: str,
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict], int]:
        from utils.script_parser import ScriptParser

        messages = self._prompt_builder.build_script_generation_messages(outline_content)
        logger.info(f"调用文本模型生成剧本（流式），模型：{self._resolve_model(model)}")

        (title, scenes), task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="scenes",
            parse_item=ScriptParser.parse_scene_item,
            parse_full=ScriptParser.parse,
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本生成",
            caller_type=GenerateTaskCallerType.SCRIPT,
        )
        logger.info(f"剧本流式生成完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes, task_id

    def optimize_screenplay_stream(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict], int]:
        from utils.script_parser import ScriptParser

        messages = self._prompt_builder.build_screenplay_optimization_messages(
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_requirement,
        )
        logger.info(f"调用文本模型优化剧本（流式），模型：{self._resolve_model(model)}")

        (title, scenes), task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="scenes",
            parse_item=ScriptParser.parse_scene_item,
            parse_full=ScriptParser.parse,
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本优化",
            caller_type=GenerateTaskCallerType.SCRIPT,
        )
        logger.info(f"剧本流式优化完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes, task_id

    def generate_storyboard_stream(
        self,
        script_content: str,
        art_style: str = "",
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        from utils.shot_parser import ShotParser

        messages = self._prompt_builder.build_storyboard_generation_messages(
            script_content=script_content,
            art_style=art_style,
        )
        logger.info(
            f"调用文本模型生成分镜（流式），模型：{self._resolve_model(model)}，"
            f"风格：{art_style or '默认'}"
        )

        shots, task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="storyboard",
            parse_item=ShotParser.parse_shot_item,
            parse_full=lambda content: (ShotParser.parse(content),),
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜生成",
            caller_type=GenerateTaskCallerType.STORYBOARD,
        )
        logger.info(f"分镜流式生成完成：共 {len(shots[0])} 个镜头")
        return shots[0], task_id

    def optimize_storyboard_stream(
        self,
        outline_content: str,
        script_content: str,
        character_content: str,
        current_storyboard: str,
        user_requirement: str,
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        from utils.shot_parser import ShotParser

        messages = self._prompt_builder.build_storyboard_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_requirement,
        )
        logger.info(f"调用文本模型优化分镜（流式），模型：{self._resolve_model(model)}")

        shots, task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="storyboard",
            parse_item=ShotParser.parse_shot_item,
            parse_full=lambda content: (ShotParser.parse(content),),
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜优化",
            caller_type=GenerateTaskCallerType.STORYBOARD,
        )
        logger.info(f"分镜流式优化完成：共 {len(shots[0])} 个镜头")
        return shots[0], task_id

    def generate_storyboard(
        self,
        script_content: str,
        art_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        messages = self._prompt_builder.build_storyboard_generation_messages(
            script_content=script_content,
            art_style=art_style,
        )

        logger.info(f"调用文本模型生成分镜，模型：{self._resolve_model(model)}，风格：{art_style or '默认'}")
        storyboard_content, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜生成",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=str(project_id) if project_id else "",
            max_tokens=16384,
        )

        logger.info("分镜生成成功")

        from utils.shot_parser import ShotParser

        try:
            shots = ShotParser.parse(storyboard_content)
        except ValueError as e:
            GenerateTaskRecorder(self._sm).mark_failed(task_id, f"解析响应失败：{e}")
            raise RuntimeError(f"解析响应失败：{e}") from e

        logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")
        return shots, task_id

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
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_design_image_prompt_messages(
            content=content,
            shot_size=shot_size,
            camera_movement=camera_movement,
            notes=notes,
            character_info=character_info,
            visual_style=visual_style,
        )

        logger.info(f"调用文本模型生成设计图提示词，模型：{self._resolve_model(model)}，风格：{visual_style or '默认'}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜设计图提示词生成",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=str(project_id) if project_id else "",
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
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_character_design_image_prompt_messages(
            character_name=character_name,
            description=description,
            user_requirement=user_requirement,
            visual_style=visual_style,
        )

        logger.info(
            f"调用文本模型生成角色设计图提示词，模型：{self._resolve_model(model)}，"
            f"角色：{character_name}，风格：{visual_style or '默认'}"
        )
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context=f"角色设计图提示词生成 - {character_name}",
            caller_type=GenerateTaskCallerType.CHARACTER,
            caller_id=str(project_id) if project_id else "",
        )

    def optimize_screenplay(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, list[dict], int]:
        messages = self._prompt_builder.build_screenplay_optimization_messages(
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化剧本，模型：{self._resolve_model(model)}")
        result, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="script",
            context="剧本优化",
            caller_type=GenerateTaskCallerType.SCRIPT,
            caller_id=str(project_id) if project_id else "",
        )

        from utils.script_parser import ScriptParser
        title, scenes = ScriptParser.parse(result)
        logger.info(f"剧本解析成功：标题='{title}'，共 {len(scenes)} 场")

        return title, scenes, task_id

    def generate_characters(
        self,
        outline_content: str,
        script_content: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        messages = self._prompt_builder.build_character_generation_messages(
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型生成角色，模型：{self._resolve_model(model)}")
        result, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色生成",
            caller_type=GenerateTaskCallerType.CHARACTER,
            caller_id=str(project_id) if project_id else "",
        )

        from utils.character_parser import CharacterParser
        characters = CharacterParser.parse(result)
        logger.info(f"角色解析成功：共 {len(characters)} 个角色")
        return characters, task_id

    def generate_characters_stream(
        self,
        outline_content: str,
        script_content: str,
        user_requirement: str,
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        from utils.character_parser import CharacterParser

        messages = self._prompt_builder.build_character_generation_messages(
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_requirement,
        )
        logger.info(f"调用文本模型生成角色（流式），模型：{self._resolve_model(model)}")

        characters, task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="characters",
            parse_item=CharacterParser.parse_character_item,
            parse_full=lambda content: (CharacterParser.parse(content),),
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色生成",
            caller_type=GenerateTaskCallerType.CHARACTER,
        )
        logger.info(f"角色流式生成完成：共 {len(characters[0])} 个角色")
        return characters[0], task_id

    def optimize_characters_stream(
        self,
        outline_content: str,
        script_content: str,
        current_characters: str,
        user_requirement: str,
        on_item: Callable[[dict], None] | None = None,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        from utils.character_parser import CharacterParser

        messages = self._prompt_builder.build_character_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_requirement,
        )
        logger.info(f"调用文本模型优化角色（流式），模型：{self._resolve_model(model)}")

        characters, task_id = self._stream_and_parse_items(
            messages=messages,
            array_key="characters",
            parse_item=CharacterParser.parse_character_item,
            parse_full=lambda content: (CharacterParser.parse(content),),
            on_item=on_item,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色优化",
            caller_type=GenerateTaskCallerType.CHARACTER,
        )
        logger.info(f"角色流式优化完成：共 {len(characters[0])} 个角色")
        return characters[0], task_id

    def optimize_characters(
        self,
        outline_content: str,
        script_content: str,
        current_characters: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[list[dict], int]:
        messages = self._prompt_builder.build_character_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化角色，模型：{self._resolve_model(model)}")
        result, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context="角色优化",
            caller_type=GenerateTaskCallerType.CHARACTER,
            caller_id=str(project_id) if project_id else "",
        )

        from utils.character_parser import CharacterParser
        characters = CharacterParser.parse(result)
        logger.info(f"角色解析成功：共 {len(characters)} 个角色")
        return characters, task_id

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
    ) -> tuple[list[dict], int]:
        messages = self._prompt_builder.build_storyboard_optimization_messages(
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型优化分镜，模型：{self._resolve_model(model)}")
        result, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜优化",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=str(project_id) if project_id else "",
        )

        from utils.shot_parser import ShotParser

        shots = ShotParser.parse(result)
        logger.info(f"分镜解析成功：共 {len(shots)} 个镜头")
        return shots, task_id

    def refine_character_description(
        self,
        character_name: str,
        current_description: str,
        user_requirement: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_character_description_refine_messages(
            character_name=character_name,
            current_description=current_description,
            user_requirement=user_requirement,
        )

        logger.info(f"调用文本模型修改角色描述，角色：{character_name}，模型：{self._resolve_model(model)}")
        result, task_id = self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context=f"角色描述优化 - {character_name}",
            caller_type=GenerateTaskCallerType.CHARACTER,
            caller_id=str(project_id) if project_id else "",
        )
        return result.strip(), task_id

    def generate_cover_image_prompt(
        self,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_info: str,
        visual_style: str = "",
        model: str | None = None,
        project_id: int | None = None,
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_cover_image_prompt_messages(
            project_name=project_name,
            aspect_ratio=aspect_ratio,
            outline_content=outline_content,
            character_info=character_info,
            visual_style=visual_style,
        )

        logger.info(f"调用文本模型生成封面图提示词，项目：{project_name}，模型：{self._resolve_model(model)}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="cover",
            context="项目封面图提示词生成",
            caller_type=GenerateTaskCallerType.COVER,
            caller_id=str(project_id) if project_id else "",
        )

    def clean_video_prompt(
        self,
        original_prompt: str,
        model: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> tuple[str, int]:
        messages = self._prompt_builder.build_video_prompt_clean_messages(original_prompt)

        logger.info(f"调用文本模型清理视频提示词，模型：{self._resolve_model(model)}")
        return self.chat(
            messages=messages,
            model=model,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="视频提示词清理",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=str(project_id) if project_id else "",
        )
