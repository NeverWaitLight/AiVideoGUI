from loguru import logger
import os
from typing import Any

import requests

from config.url_resolver import get_image_url
from models.enums import GenerateTaskType
from models.generate_task_context import GenerateTaskContext
from models.provider_config import ProviderConfig
from prompts.image_prompt_builder import ImagePromptBuilder
from providers.generate_task_recorder import GenerateTaskRecorder
from providers.image_base import ImageProvider


class DashScopeImageProvider(ImageProvider):

    DEFAULT_MODEL = "wan2.6-t2i"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        submit_url = get_image_url(config)
        if not submit_url:
            raise RuntimeError("DashScope 图片 provider 未配置 base_url")
        self._api_key = config.api_key
        self._submit_url = submit_url
        self._model = config.default_model or self.DEFAULT_MODEL

    @property
    def submit_url(self) -> str:
        return self._submit_url

    def build_headers(self) -> dict[str, str]:
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
        task_context: GenerateTaskContext | None = None,
    ) -> tuple[str, dict[str, Any], int | None]:
        payload = ImagePromptBuilder.build_bailian_image_payload(
            prompt=prompt,
            size=size,
            negative_prompt=negative_prompt,
            n=n,
            prompt_extend=prompt_extend,
            watermark=watermark,
            seed=seed,
            model=self._model,
        )

        child_task_id: int | None = None
        recorder: GenerateTaskRecorder | None = None
        if task_context is not None:
            recorder = GenerateTaskRecorder(task_context.session_manager)
            _, child_task_id = recorder.create_pending(
                provider_name=self.provider_name,
                model_name=self._model,
                request_params=payload,
                task_type=GenerateTaskType.IMAGE,
                local_path=task_context.local_path,
                caller_type=task_context.caller_type,
                caller_id=task_context.caller_id,
                project_id=task_context.project_id,
                parent_ids=task_context.parent_ids,
            )
            logger.info(
                f"图片生成子任务已创建：task_id={child_task_id}, parent_ids={task_context.parent_ids}"
            )

        logger.info(f"提交图片生成任务，模型：{self._model}，尺寸：{size}，数量：{n}")
        logger.info(f"图片生成请求 URL：{self.submit_url}")
        logger.info(f"图片生成请求体：{payload}")

        max_retries = 2
        timeout = 1800
        resp = None

        try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"发起请求（第 {attempt + 1}/{max_retries} 次尝试）")
                    resp = requests.post(
                        self.submit_url,
                        json=payload,
                        headers=self.build_headers(),
                        timeout=timeout,
                    )
                    logger.info(f"图片生成响应状态码：{resp.status_code}")
                    logger.info(f"图片生成响应体：{resp.text}")
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        logger.warning(f"请求超时（{timeout}秒），准备重试...")
                        continue
                    logger.error(f"请求超时（{timeout}秒），已重试 {max_retries} 次，放弃")
                    raise RuntimeError(
                        f"图片生成请求超时（{timeout}秒），请检查网络连接或稍后重试"
                    )
                except requests.exceptions.RequestException as e:
                    logger.exception("提交图片生成任务网络请求失败")
                    raise RuntimeError(f"网络请求失败：{e}") from e

            if resp is None or not resp.ok:
                try:
                    error_data = resp.json() if resp is not None else {}
                    code = error_data.get("code", "")
                    message = error_data.get("message", "")
                    error_detail = f"[{code}] {message}" if code else (message or (resp.text if resp else ""))
                except Exception:
                    error_detail = resp.text if resp is not None else "未知错误"
                status_code = resp.status_code if resp is not None else 0
                logger.error(f"DashScope 图片 API 返回 {status_code}: {error_detail}")
                raise RuntimeError(f"DashScope 图片 API 错误 ({status_code}): {error_detail}")

            data = resp.json()
            logger.info(f"图片生成响应解析：{data}")

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
            if recorder is not None and child_task_id is not None:
                recorder.mark_succeeded(child_task_id, remote_url=image_url)
            return image_url, payload, child_task_id

        except Exception as e:
            if recorder is not None and child_task_id is not None:
                recorder.mark_failed(child_task_id, str(e))
            raise

    def download(self, image_url: str, save_path: str) -> str:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info(f"下载图片：{image_url} -> {save_path}")

        try:
            with requests.get(image_url, stream=True, timeout=60) as resp:
                logger.info(f"图片下载响应状态码：{resp.status_code}")
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            logger.exception("下载图片失败")
            raise RuntimeError(f"下载图片失败：{e}") from e

        logger.info(f"图片下载完成：{save_path}")
        return save_path

    def list_available_models(self) -> list[str]:
        """返回 DashScope 支持的图片模型列表"""
        return ["wan2.6-t2i"]
