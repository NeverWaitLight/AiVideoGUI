from loguru import logger

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope_image": DashScopeImageProvider,
}

class ImageService:

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager
        self._providers: dict[str, ImageProvider] = {}

    def _get_provider(self) -> ImageProvider:
        provider_name = self._config.settings.default_image_provider or "dashscope_image"

        if provider_name not in _PROVIDER_REGISTRY:
            logger.warning(f"未知的图片供应商 {provider_name}，回退到 dashscope_image")
            provider_name = "dashscope_image"

        if provider_name in self._providers:
            return self._providers[provider_name]

        provider_cfg = self._config.get_provider(provider_name)
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
    ) -> str:
        provider = self._get_provider()

        logger.info(f"提交图片生成任务，尺寸：{size}，数量：{n}")
        logger.debug(f"Prompt: {prompt}")

        image_url = provider.generate(
            prompt=prompt,
            size=size,
            negative_prompt=negative_prompt,
            n=n,
            prompt_extend=True,
            watermark=False,
        )

        return provider.download(image_url, save_path)
