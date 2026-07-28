"""DashScope万相文生图 Provider。

使用万相 wan2.6-t2i 模型生成图片，支持同步调用模式。
API 文档：https://help.aliyun.com/zh/model-studio/getting-started/models/wanx-image-generation-api
"""

from loguru import logger
import os
from typing import Any

import requests

from models.data_models import ProviderConfig
from providers.image_base import ImageProvider

class DashScopeImageProvider(ImageProvider):
    """DashScope万相文生图实现（wan2.6-t2i）。"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    SUBMIT_URL = f"{BASE_URL}/services/aigc/multimodal-generation/generation"
    DEFAULT_MODEL = "wan2.6-t2i"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_key = config.api_key
        self._model = config.default_model or self.DEFAULT_MODEL

    def _headers(self) -> dict[str, str]:
        """构建请求头。"""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        prompt: str,
        size: str = "1280*1280",
        negative_prompt: str = "",
        n: int = 1,
        prompt_extend: bool = True,
        watermark: bool = False,
        seed: int | None = None,
    ) -> str:
        """同步生成图片并返回图片 URL。

        Args:
            prompt: 正向提示词（中英文，最多 2100 字符）
            size: 图片尺寸，格式 "宽*高"，默认 "1280*1280"
                  常见比例推荐：
                  - 1:1 → 1280*1280
                  - 3:4 → 1104*1472
                  - 4:3 → 1472*1104
                  - 9:16 → 960*1696
                  - 16:9 → 1696*960
            negative_prompt: 反向提示词（不希望出现的内容，最多 500 字符）
            n: 生成图片数量（1-4），默认 1（按张计费，测试建议设为 1）
            prompt_extend: 是否开启提示词智能改写（增加 3-4 秒耗时）
            watermark: 是否添加水印（右下角 "AI生成"）
            seed: 随机数种子（0-2147483647），保持相对稳定

        Returns:
            图片 URL（有效期 24 小时，需及时下载）

        Raises:
            RuntimeError: API 调用失败
        """
        payload = {
            "model": self._model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": n,
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
            },
        }

        # 可选参数：seed
        if seed is not None:
            payload["parameters"]["seed"] = seed

        logger.info(f"提交图片生成任务，模型：{self._model}，尺寸：{size}，数量：{n}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.SUBMIT_URL,
                json=payload,
                headers=self._headers(),
                timeout=120,  # wan2.6 同步调用可能需要较长时间
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")
        except requests.exceptions.RequestException as e:
            logger.exception("提交图片生成任务失败")
            raise RuntimeError(f"网络请求失败：{e}")

        # 解析响应（wan2.6 同步调用格式）
        output = data.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            code = data.get("code", "")
            message = data.get("message", "未知错误")
            error = f"[{code}] {message}" if code else message
            logger.error(f"图片生成失败：{error}")
            raise RuntimeError(f"图片生成失败：{error}")

        # 提取第一张图片 URL
        first_choice = choices[0]
        message_obj = first_choice.get("message", {})
        content = message_obj.get("content", [])

        if not content:
            raise RuntimeError("API 未返回图片内容")

        image_url = content[0].get("image", "")
        if not image_url:
            raise RuntimeError("API 未返回图片 URL")

        logger.info(f"图片生成成功：{image_url}")
        return image_url

    def download(self, image_url: str, save_path: str) -> str:
        """下载图片到本地路径。

        Args:
            image_url: 图片 URL（有效期 24 小时）
            save_path: 本地保存路径

        Returns:
            保存后的本地文件路径

        Raises:
            RuntimeError: 下载失败
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info(f"下载图片：{image_url} -> {save_path}")

        try:
            with requests.get(image_url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            logger.exception("下载图片失败")
            raise RuntimeError(f"下载图片失败：{e}")

        logger.info(f"图片下载完成：{save_path}")
        return save_path
