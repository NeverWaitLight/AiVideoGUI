from loguru import logger

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from utils.ai_request_logger import AIRequestLogger

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope_image": DashScopeImageProvider,
}

class ImageService:

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_request_logger: AIRequestLogger | None = None,
    ) -> None:
        self._config = config_manager
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
        save_path: str,
        size: str = "1696*960",
        negative_prompt: str = "",
        n: int = 1,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
    ) -> str:
        provider = self._get_provider()

        logger.info(f"提交图片生成任务，尺寸：{size}，数量：{n}")
        logger.debug(f"Prompt: {prompt}")

        image_url, request_payload = provider.generate(
            prompt=prompt,
            size=size,
            negative_prompt=negative_prompt,
            n=n,
            prompt_extend=True,
            watermark=False,
        )

        # 记录 AI 请求（与文本模型日志格式一致，包含完整 HTTP 请求信息）
        if self._ai_logger:
            self._ai_logger.log_request(
                request_type="image_generation",
                module=module,
                payload={
                    "url": provider.submit_url,
                    "json": request_payload,
                    "headers": provider.build_headers(),
                },
                response={"image_url": image_url, "save_path": save_path},
                project_id=project_id,
                project_name=project_name,
                context=context or "图片生成",
            )

        return provider.download(url=image_url, save_path=save_path)
