"""图片生成服务：调用 DashScope 文生图 API 生成分镜设计图。"""

import logging
import os
import time

import requests

from config.manager import ConfigManager
from utils import paths

logger = logging.getLogger(__name__)


class ImageService:
    """图片生成服务：通过 DashScope 文生图 API 生成分镜设计图。"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    SUBMIT_URL = f"{BASE_URL}/services/aigc/text2image/image-synthesis"
    TASK_URL = f"{BASE_URL}/tasks"
    DEFAULT_MODEL = "z-image-turbo"

    POLL_INTERVAL = 3
    MAX_POLLS = 60

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def _get_config(self) -> tuple[str, str]:
        """获取图片生成供应商的 API Key 和模型名称。"""
        provider_name = self._config.settings.default_image_provider or "bailian_image"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")
        model = provider_cfg.default_model or self.DEFAULT_MODEL
        return provider_cfg.api_key, model

    def generate(
        self,
        prompt: str,
        save_path: str,
        size: str = "1280*720",
    ) -> str:
        """同步生成设计图并保存到本地。

        Args:
            prompt: 英文图片生成提示词
            save_path: 本地保存路径
            size: 图片尺寸（默认 1280*720，16:9）

        Returns:
            保存后的本地文件路径

        Raises:
            RuntimeError: API 调用失败或生成失败
        """
        api_key, model = self._get_config()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "size": size,
                "n": 1,
            },
        }

        logger.info(f"提交图片生成任务，模型：{model}，尺寸：{size}")
        logger.debug(f"请求体：{payload}")

        try:
            resp = requests.post(
                self.SUBMIT_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"提交响应：{data}")
        except requests.exceptions.RequestException as e:
            logger.exception("提交图片生成任务失败")
            raise RuntimeError(f"网络请求失败：{e}")

        output = data.get("output", {})
        task_id = output.get("task_id", "")
        if not task_id:
            raise RuntimeError(f"API 未返回 task_id：{data}")

        logger.info(f"图片生成任务已提交，task_id={task_id}")

        # 轮询任务状态
        image_url = self._poll_task(task_id, api_key)

        # 下载图片
        return self._download_image(image_url, save_path)

    def _poll_task(self, task_id: str, api_key: str) -> str:
        """轮询任务状态直到完成，返回图片 URL。"""
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        url = f"{self.TASK_URL}/{task_id}"

        for i in range(self.MAX_POLLS):
            time.sleep(self.POLL_INTERVAL)
            try:
                resp = requests.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"轮询任务状态失败（第 {i + 1} 次）：{e}")
                continue

            output = data.get("output", {})
            status = output.get("task_status", "")
            logger.debug(f"任务状态（第 {i + 1} 次）：{status}")

            if status == "SUCCEEDED":
                results = output.get("results", [])
                if results and isinstance(results, list):
                    image_url = results[0].get("url", "")
                    if image_url:
                        logger.info(f"图片生成成功：{image_url}")
                        return image_url
                raise RuntimeError("任务成功但未返回图片 URL")

            if status == "FAILED":
                code = output.get("code", "")
                message = output.get("message", "未知错误")
                error = f"[{code}] {message}" if code else message
                logger.error(f"图片生成任务失败：{error}")
                raise RuntimeError(f"图片生成失败：{error}")

        raise RuntimeError(f"图片生成超时（已等待 {self.MAX_POLLS * self.POLL_INTERVAL} 秒）")

    def _download_image(self, image_url: str, save_path: str) -> str:
        """下载图片到本地路径。"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info(f"下载设计图：{image_url} -> {save_path}")

        try:
            with requests.get(image_url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            logger.exception("下载设计图失败")
            raise RuntimeError(f"下载图片失败：{e}")

        logger.info(f"设计图下载完成：{save_path}")
        return save_path
