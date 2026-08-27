from collections.abc import Callable

from loguru import logger

import any_llm
from any_llm.provider import ProviderFactory

from config.url_resolver import get_chat_base_url
from models.enums import GenerateTaskType
from models.generate_task_context import GenerateTaskContext
from models.provider_config import ProviderConfig
from providers.chat_base import ChatProvider
from providers.generate_task_recorder import GenerateTaskRecorder

_DEFAULT_TIMEOUT = 1800.0


def _catalog_provider_id(provider_name: str) -> str:
    if provider_name.endswith("_chat"):
        return provider_name[:-5]
    return provider_name


def _supported_providers() -> set[str]:
    return set(ProviderFactory.get_supported_providers())


def _require_supported_provider(provider_id: str) -> str:
    supported = _supported_providers()
    if provider_id not in supported:
        supported_text = ", ".join(sorted(supported))
        raise RuntimeError(
            f"供应商 {provider_id} 不在 any-llm 支持列表中。当前支持：{supported_text}"
        )
    return provider_id


class AnyLLMChatProvider(ChatProvider):
    """基于 any-llm-sdk 的统一文本模型 ChatProvider 实现"""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_base = get_chat_base_url(config)
        self._anyllm_provider_key = _require_supported_provider(
            _catalog_provider_id(config.provider_name)
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        task_context: GenerateTaskContext | None = None,
        **kwargs,
    ) -> tuple[str, int | None]:
        return self._execute_chat(
            messages,
            model,
            task_context,
            stream=False,
            on_chunk=None,
            **kwargs,
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        task_context: GenerateTaskContext | None = None,
        on_chunk: Callable[[str], None] | None = None,
        **kwargs,
    ) -> tuple[str, int | None]:
        return self._execute_chat(
            messages,
            model,
            task_context,
            stream=True,
            on_chunk=on_chunk,
            **kwargs,
        )

    def _execute_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None,
        task_context: GenerateTaskContext | None,
        stream: bool,
        on_chunk: Callable[[str], None] | None,
        **kwargs,
    ) -> tuple[str, int | None]:
        resolved_model = self._resolve_model(model)
        task_id = self._create_chat_task(
            task_context, resolved_model, messages, stream, **kwargs
        )

        try:
            if stream:
                content = self._call_api_stream(
                    messages, resolved_model, on_chunk=on_chunk, **kwargs
                )
            else:
                content = self._call_api(messages, resolved_model, **kwargs)
        except Exception as e:
            self._fail_chat_task(task_context, task_id, e)
            raise

        self._complete_chat_task(task_context, task_id, content)
        return content, task_id

    def _create_chat_task(
        self,
        task_context: GenerateTaskContext | None,
        resolved_model: str,
        messages: list[dict[str, str]],
        stream: bool,
        **kwargs,
    ) -> int | None:
        if task_context is None:
            return None

        request_params = {
            "messages": messages,
            "model": resolved_model,
            "module": task_context.module,
            "context": task_context.context,
            "project_id": task_context.project_id,
            "project_name": task_context.project_name,
            "stream": stream,
            **kwargs,
        }
        recorder = GenerateTaskRecorder(task_context.session_manager)
        _, task_id = recorder.create_pending(
            provider_name=self.provider_name,
            model_name=resolved_model,
            request_params=request_params,
            task_type=GenerateTaskType.CHAT,
            caller_type=task_context.caller_type,
            caller_id=task_context.caller_id,
            project_id=task_context.project_id,
            parent_ids=task_context.parent_ids,
        )
        mode_label = "流式" if stream else ""
        logger.info(
            f"文本{mode_label}对话子任务已创建：task_id={task_id}, model={resolved_model}, "
            f"parent_ids={task_context.parent_ids}"
        )
        return task_id

    def _complete_chat_task(
        self,
        task_context: GenerateTaskContext | None,
        task_id: int | None,
        content: str,
    ) -> None:
        if task_id is not None and task_context is not None:
            GenerateTaskRecorder(task_context.session_manager).mark_succeeded(
                task_id, response_data=content
            )

    def _fail_chat_task(
        self,
        task_context: GenerateTaskContext | None,
        task_id: int | None,
        error: Exception,
    ) -> None:
        if task_id is not None and task_context is not None:
            GenerateTaskRecorder(task_context.session_manager).mark_failed(task_id, str(error))

    def _call_api(
        self,
        messages: list[dict[str, str]],
        resolved_model: str,
        **kwargs,
    ) -> str:
        params = {**self._config.default_params, **kwargs}

        logger.info(f"调用文本模型：provider={self.provider_name}, model={resolved_model}")

        try:
            completion_kwargs: dict = {
                "model": resolved_model,
                "messages": messages,
                "api_key": self._config.api_key,
                "api_timeout": _DEFAULT_TIMEOUT,
                **params,
            }
            if self._api_base:
                completion_kwargs["api_base"] = self._api_base

            response = any_llm.completion(**completion_kwargs)
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            logger.exception(f"文本模型调用失败：{e}")
            raise RuntimeError(f"文本模型调用失败：{e}") from e

    def _call_api_stream(
        self,
        messages: list[dict[str, str]],
        resolved_model: str,
        on_chunk: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        params = {**self._config.default_params, **kwargs}

        logger.info(
            f"调用文本模型（流式）：provider={self.provider_name}, model={resolved_model}"
        )

        try:
            completion_kwargs: dict = {
                "model": resolved_model,
                "messages": messages,
                "api_key": self._config.api_key,
                "api_timeout": _DEFAULT_TIMEOUT,
                "stream": True,
                **params,
            }
            if self._api_base:
                completion_kwargs["api_base"] = self._api_base

            stream = any_llm.completion(**completion_kwargs)
            parts: list[str] = []
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue
                parts.append(delta)
                if on_chunk is not None:
                    on_chunk(delta)
            return "".join(parts).strip()
        except Exception as e:
            logger.exception(f"文本模型流式调用失败：{e}")
            raise RuntimeError(f"文本模型调用失败：{e}") from e

    def _resolve_model(self, model: str | None = None) -> str:
        model_name = model or self._config.default_model
        if not model_name:
            raise ValueError("未配置默认模型")

        if "/" in model_name:
            provider_id, model_id = model_name.split("/", 1)
            if not provider_id.strip():
                raise ValueError(f"模型格式无效：{model_name}")
            if not model_id.strip():
                raise ValueError(f"未指定模型名称：{model_name}")
            _require_supported_provider(provider_id.strip())
            return f"{provider_id.strip()}/{model_id.strip()}"

        return f"{self._anyllm_provider_key}/{model_name}"
