"""图片生成服务：调用文生图 API 生成分镜设计图。"""

from loguru import logger

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope_image": DashScopeImageProvider,
}

class ImageService:
    """图片生成服务：通过文生图 API 生成分镜设计图。"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager
        self._providers: dict[str, ImageProvider] = {}

    def _get_provider(self) -> ImageProvider:
        """获取或创建 Provider 实例（延迟加载 + 缓存）。"""
        provider_name = self._config.settings.default_image_provider or "dashscope_image"

        # 未知 provider 回退到 dashscope_image（兼容旧配置）
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
        """同步生成设计图并保存到本地。

        Args:
            prompt: 图片生成提示词（中英文，最多 2100 字符）
            save_path: 本地保存路径
            size: 图片尺寸（默认 1696*960，16:9）
                  常见比例推荐：
                  - 1:1 → 1280*1280
                  - 3:4 → 1104*1472
                  - 4:3 → 1472*1104
                  - 9:16 → 960*1696
                  - 16:9 → 1696*960
            negative_prompt: 反向提示词（不希望出现的内容）
            n: 生成图片数量（1-4），默认 1

        Returns:
            保存后的本地文件路径

        Raises:
            RuntimeError: API 调用失败或生成失败
        """
        provider = self._get_provider()

        logger.info(f"提交图片生成任务，尺寸：{size}，数量：{n}")
        logger.debug(f"Prompt: {prompt}")

        # 调用 Provider 生成图片（同步调用）
        image_url = provider.generate(
            prompt=prompt,
            size=size,
            negative_prompt=negative_prompt,
            n=n,
            prompt_extend=True,
            watermark=False,
        )

        # 下载图片到本地
        return provider.download(image_url, save_path)
