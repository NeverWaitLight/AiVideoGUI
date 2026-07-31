from loguru import logger
import os
from typing import Any

import requests

from models.provider_config import ProviderConfig
from providers.image_base import ImageProvider

class DashScopeImageProvider(ImageProvider):

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    SUBMIT_URL = f"{BASE_URL}/services/aigc/multimodal-generation/generation"
    DEFAULT_MODEL = "wan2.6-t2i"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_key = config.api_key
        self._model = config.default_model or self.DEFAULT_MODEL

    def _headers(self) -> dict[str, str]:
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

        if seed is not None:
            payload["parameters"]["seed"] = seed

        logger.info(f"提交图片生成任务，模型：{self._model}，尺寸：{size}，数量：{n}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.SUBMIT_URL,
                json=payload,
                headers=self._headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"响应：{data}")
        except requests.exceptions.RequestException as e:
            logger.exception("提交图片生成任务失败")
            raise RuntimeError(f"网络请求失败：{e}")

        output = data.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            code = data.get("code", "")
            message = data.get("message", "未知错误")
            error = f"[{code}] {message}" if code else message
            logger.error(f"图片生成失败：{error}")
            raise RuntimeError(f"图片生成失败：{error}")

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
