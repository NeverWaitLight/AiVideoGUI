import json
import time
import uuid
from loguru import logger

from config.manager import ConfigManager
from models.enums import GenerateTaskType, GenerateTaskCallerType
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from utils.ai_request_logger import AIRequestLogger

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope_image": DashScopeImageProvider,
}

# 配置名称映射到实际 Provider 名称
_CONFIG_TO_PROVIDER_NAME: dict[str, str] = {
    "dashscope_image": "dashscope",  # 配置使用 dashscope_image，存储使用 dashscope
}

class ImageService:

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        ai_request_logger: AIRequestLogger | None = None,
    ) -> None:
        self._config = config_manager
        self._sm = session_manager
        self._providers: dict[str, ImageProvider] = {}
        self._ai_logger = ai_request_logger

    def _get_provider(self) -> ImageProvider:
        provider_name = self._config.settings.default_image_provider or "dashscope_image"

        if provider_name not in _PROVIDER_REGISTRY:
            logger.warning(f"未知的图片供应商 {provider_name}，回退到 dashscope_image")
            provider_name = "dashscope_image"

        if provider_name in self._providers:
            return self._providers[provider_name]

        provider_cfg = self._config.resolve_config_for_type(name=provider_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        cls = _PROVIDER_REGISTRY.get(provider_name)

        provider = cls(provider_cfg)
        self._providers[provider_name] = provider
        logger.info(f"初始化图片生成 Provider：{provider_name}")
        return provider

    def generate(
        self,
        prompt: str,
        local_path: str,
        size: str = "1696*960",
        negative_prompt: str = "",
        n: int = 1,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
    ) -> str:
        """提交图片生成任务到数据库，返回 provider_task_id"""
        # 配置名称（用于读取配置）
        config_name = "dashscope_image"
        # 存储名称（用于数据库存储和显示）
        provider_name = _CONFIG_TO_PROVIDER_NAME.get(config_name, "dashscope")

        provider_cfg = self._config.resolve_config_for_type(name=config_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {config_name} 的 API Key，请在设置中配置")

        provider_task_id = str(uuid.uuid4())

        request_params = json.dumps({
            "prompt": prompt,
            "size": size,
            "negative_prompt": negative_prompt,
            "n": n,
            "module": module,
            "context": context,
            "config_name": config_name,  # 记录配置名称，用于后续查找
        }, ensure_ascii=False)

        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.add(
                provider_task_id=provider_task_id,
                provider_name=provider_name,  # 存储简化的名称
                model_name=provider_cfg.default_model or "wan2.6-t2i",
                local_path=local_path,
                request_params=request_params,
                type=GenerateTaskType.IMAGE,
                caller_type=caller_type,
                caller_id=caller_id,
                parent_ids=parent_ids,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

        logger.info(f"图片生成任务已提交：task_id={provider_task_id}, provider={provider_name}, config={config_name}, size={size}, caller_type={caller_type}, caller_id={caller_id}, parent_ids={parent_ids}")
        return provider_task_id
