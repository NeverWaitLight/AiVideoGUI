"""图片生成后台任务 Worker（在独立线程中执行 HTTP 请求）"""
import json
import os
from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope": DashScopeImageProvider,
    "dashscope_image": DashScopeImageProvider,
}


class _ImageSignalEmitter(QObject):
    task_finished = Signal(str)  # provider_task_id
    task_failed = Signal(str, str)  # provider_task_id, error_message


_signal_emitter = _ImageSignalEmitter()


def get_image_signal_emitter() -> _ImageSignalEmitter:
    return _signal_emitter


def _mark_task_failed(
    session_manager: SessionManager,
    provider_task_id: str,
    error_msg: str,
) -> None:
    try:
        task_repo = session_manager.get_repo(repo_class=GenerateTaskRepository)
        task_info = task_repo.get_by_provider_task_id(provider_task_id)
        if not task_info:
            return
        if task_info.get("completed"):
            return
        session_manager.begin_write()
        try:
            task_repo.update_status(task_info["id"], "failed", error_message=error_msg)
            task_repo.mark_completed(task_info["id"])
            session_manager.commit_write()
        except Exception:
            session_manager.rollback_write()
            raise
    except Exception as db_error:
        logger.error(f"更新任务失败状态时出错：{db_error}")


def execute_image_generation(
    provider_task_id: str,
    config_manager: ConfigManager,
    session_manager: SessionManager,
    workspace_root: str,
) -> str:
    """同步执行图片生成：调用 HTTP 接口、下载图片、更新 generate_task 状态。

    返回下载后的本地绝对路径。失败时抛出异常。
    """
    try:
        task_repo = session_manager.get_repo(repo_class=GenerateTaskRepository)
        task_info = task_repo.get_by_provider_task_id(provider_task_id)

        if not task_info:
            raise RuntimeError(f"任务不存在：{provider_task_id}")

        provider_name = task_info["provider_name"]
        local_path = task_info["local_path"]
        request_params = json.loads(task_info["request_params"])

        prompt = request_params.get("prompt", "")
        size = request_params.get("size", "1696*960")
        negative_prompt = request_params.get("negative_prompt", "")
        n = request_params.get("n", 1)
        config_name = request_params.get("config_name")

        logger.info(f"开始生成图片：task_id={provider_task_id}, provider={provider_name}, config={config_name}, size={size}")

        session_manager.begin_write()
        try:
            task_repo.update_status(task_info["id"], "running")
            session_manager.commit_write()
        except Exception:
            session_manager.rollback_write()
            raise

        if not config_name:
            config_name = provider_name

        provider_cfg = config_manager.resolve_config_for_type(name=config_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {config_name} 的 API Key")

        cls = _PROVIDER_REGISTRY.get(config_name) or _PROVIDER_REGISTRY.get(provider_name)
        if not cls:
            raise RuntimeError(f"未知的图片供应商：{config_name}")

        provider = cls(provider_cfg)

        image_url, request_payload = provider.generate(
            prompt=prompt,
            size=size,
            negative_prompt=negative_prompt,
            n=n,
            prompt_extend=True,
            watermark=False,
        )

        absolute_path = os.path.join(workspace_root, local_path)
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        result_path = provider.download(image_url=image_url, save_path=absolute_path)

        session_manager.begin_write()
        try:
            task_repo.update_status(task_info["id"], "succeeded", remote_url=image_url)
            task_repo.mark_completed(task_info["id"])
            session_manager.commit_write()
        except Exception:
            session_manager.rollback_write()
            raise

        logger.info(f"图片生成完成：{result_path}")
        _signal_emitter.task_finished.emit(provider_task_id)
        return result_path

    except Exception as e:
        error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
        logger.error(f"图片生成失败：{error_msg}")
        _mark_task_failed(session_manager, provider_task_id, error_msg)
        _signal_emitter.task_failed.emit(provider_task_id, error_msg)
        raise


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
        if not config_name:
            config_name = provider_name

        cache_key = config_name
        if cache_key in self._providers:
            return self._providers[cache_key]

        provider_cfg = self._config.resolve_config_for_type(name=config_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {config_name} 的 API Key")

        cls = _PROVIDER_REGISTRY.get(config_name) or _PROVIDER_REGISTRY.get(provider_name)
        if not cls:
            raise RuntimeError(f"未知的图片供应商：{config_name}")

        provider = cls(provider_cfg)
        self._providers[cache_key] = provider
        return provider

    def run(self):
        try:
            result_path = execute_image_generation(
                provider_task_id=self._provider_task_id,
                config_manager=self._config,
                session_manager=self._sm,
                workspace_root=self._workspace_root,
            )
            logger.debug(f"发出 finished 信号：provider_task_id={self._provider_task_id}, result_path={result_path}")
            self.finished.emit(self._provider_task_id, result_path)
            logger.debug(f"finished 信号已发出，等待槽函数响应")

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            # 失败落库与全局信号已在 execute_image_generation 中处理
            self.failed.emit(self._provider_task_id, error_msg)
