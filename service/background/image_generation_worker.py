"""图片生成后台任务 Worker（在独立线程中执行 HTTP 请求）"""
import json
import os
import time
from loguru import logger
from PySide6.QtCore import QThread, Signal

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope_image": DashScopeImageProvider,
}

# Provider 名称映射到配置名称（与 ImageService 相反）
_PROVIDER_TO_CONFIG_NAME: dict[str, str] = {
    "dashscope": "dashscope_image",
}


class ImageGenerationWorker(QThread):
    """图片生成 Worker：从 generate_tasks 表读取任务，执行 HTTP 请求，更新状态"""

    finished = Signal(str, str)  # provider_task_id, image_path
    failed = Signal(str, str)  # provider_task_id, error_message

    def __init__(
        self,
        provider_task_id: str,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        workspace_root: str,
        parent=None,
    ):
        super().__init__(parent)
        self._provider_task_id = provider_task_id
        self._config = config_manager
        self._sm = session_manager
        self._workspace_root = workspace_root
        self._providers: dict[str, ImageProvider] = {}

    def _get_provider(self, provider_name: str, config_name: str | None = None) -> ImageProvider:
        """根据 provider_name 或 config_name 获取 Provider 实例"""
        # 如果没有传入 config_name，则从 provider_name 映射
        if not config_name:
            config_name = _PROVIDER_TO_CONFIG_NAME.get(provider_name, provider_name)

        # 使用 config_name 作为缓存键
        cache_key = config_name
        if cache_key in self._providers:
            return self._providers[cache_key]

        provider_cfg = self._config.resolve_config_for_type(name=config_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {config_name} 的 API Key")

        cls = _PROVIDER_REGISTRY.get(config_name)
        if not cls:
            raise RuntimeError(f"未知的图片供应商：{config_name}")

        provider = cls(provider_cfg)
        self._providers[cache_key] = provider
        return provider

    def run(self):
        try:
            task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
            task_info = task_repo.get_by_provider_task_id(self._provider_task_id)

            if not task_info:
                error_msg = f"任务不存在：{self._provider_task_id}"
                logger.error(error_msg)
                self.failed.emit(self._provider_task_id, error_msg)
                return

            provider_name = task_info["provider_name"]
            local_path = task_info["local_path"]
            request_params = json.loads(task_info["request_params"])

            prompt = request_params.get("prompt", "")
            size = request_params.get("size", "1696*960")
            negative_prompt = request_params.get("negative_prompt", "")
            n = request_params.get("n", 1)
            module = request_params.get("module", "storyboard")
            context = request_params.get("context", "图片生成")
            config_name = request_params.get("config_name")  # 可能为 None（旧数据）

            logger.info(f"开始生成图片：task_id={self._provider_task_id}, provider={provider_name}, config={config_name}, size={size}")

            self._sm.begin_write()
            try:
                task_repo.update_status(task_info["id"], "running")
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            provider = self._get_provider(provider_name, config_name)

            image_url, request_payload = provider.generate(
                prompt=prompt,
                size=size,
                negative_prompt=negative_prompt,
                n=n,
                prompt_extend=True,
                watermark=False,
            )

            # local_path 是相对路径，需要拼接工作目录
            absolute_path = os.path.join(self._workspace_root, local_path)

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            result_path = provider.download(image_url=image_url, save_path=absolute_path)

            self._sm.begin_write()
            try:
                task_repo.update_status(task_info["id"], "succeeded", remote_url=image_url)
                task_repo.mark_completed(task_info["id"])
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            logger.info(f"图片生成完成：{result_path}")
            self.finished.emit(self._provider_task_id, result_path)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            logger.error(f"图片生成失败：{error_msg}")

            try:
                task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
                task_info = task_repo.get_by_provider_task_id(self._provider_task_id)
                if task_info:
                    self._sm.begin_write()
                    try:
                        task_repo.update_status(task_info["id"], "failed", error_message=error_msg)
                        task_repo.mark_completed(task_info["id"])
                        self._sm.commit_write()
                    except Exception:
                        self._sm.rollback_write()
            except Exception as db_error:
                logger.error(f"更新任务失败状态时出错：{db_error}")

            self.failed.emit(self._provider_task_id, error_msg)
