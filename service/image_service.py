"""图片生成服务：调用DashScope文生图 API 生成分镜设计图。"""

import logging

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider

logger = logging.getLogger(__name__)


class ImageService:
    """图片生成服务：通过DashScope万相文生图 API 生成分镜设计图。"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager
        self._provider: DashScopeImageProvider | None = None

    def _get_provider(self) -> DashScopeImageProvider:
        """获取或创建 Provider 实例（延迟加载 + 缓存）。"""
        if self._provider is not None:
            return self._provider

        provider_name = self._config.settings.default_image_provider or "dashscope_image"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        model = provider_cfg.default_model or "wan2.6-t2i"
        self._provider = DashScopeImageProvider(api_key=provider_cfg.api_key, model=model)
        logger.info(f"初始化图片生成 Provider：{provider_name}，模型：{model}")
        return self._provider

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
