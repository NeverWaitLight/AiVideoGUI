from loguru import logger

from PySide6.QtCore import QObject, QThread, Signal

from config.manager import ConfigManager
from providers.dashscope_chat import DashScopeChatProvider
from providers.chat_base import ChatProvider

_CHAT_PROVIDER_REGISTRY: dict[str, type[ChatProvider]] = {
    "dashscope": DashScopeChatProvider,
}

_TITLE_SYSTEM_PROMPT = (
    "你是一个标题生成助手。根据用户发送的消息内容，生成一个简短的对话标题（不超过15个字）。"
    "只返回标题文本，不要包含任何多余文字、引号或标点符号。"
)

class _TitleWorker(QThread):

    title_ready = Signal(str, str)
    title_failed = Signal(str, str)

    def __init__(
        self,
        provider: ChatProvider,
        conv_id: str,
        user_text: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._conv_id = conv_id
        self._user_text = user_text

    def run(self) -> None:
        try:
            messages = [
                {"role": "system", "content": _TITLE_SYSTEM_PROMPT},
                {"role": "user", "content": self._user_text},
            ]
            title = self._provider.chat(messages).strip().strip("\"'")
            self.title_ready.emit(self._conv_id, title)
        except Exception as e:
            logger.warning(f"生成标题失败 conv={self._conv_id}: {e}")
            self.title_failed.emit(self._conv_id, str(e))

class ChatService(QObject):

    title_ready = Signal(str, str)
    title_failed = Signal(str, str)

    def __init__(self, config: ConfigManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._provider: ChatProvider | None = None
        self._worker: _TitleWorker | None = None

    def _get_provider(self) -> ChatProvider:
        if self._provider is not None:
            return self._provider
        provider_name = self._config.settings.default_chat_provider or "dashscope"
        cfg = self._config.get_provider(provider_name)
        if cfg is None:
            raise KeyError(f"未配置的对话 Provider：{provider_name}")
        cls = _CHAT_PROVIDER_REGISTRY.get(provider_name)
        if cls is None:
            raise KeyError(f"未注册的对话 Provider：{provider_name}")
        self._provider = cls(cfg)
        return self._provider

    def generate_title(self, conv_id: str, user_text: str) -> None:
        try:
            provider = self._get_provider()
        except KeyError as e:
            logger.warning(f"无法生成标题：{e}")
            return

        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1000)

        self._worker = _TitleWorker(provider, conv_id, user_text)
        self._worker.title_ready.connect(self.title_ready)
        self._worker.title_failed.connect(self.title_failed)
        self._worker.finished.connect(self._cleanup)
        self._worker.start()

    def chat(self, messages: list[dict]) -> str:
        provider = self._get_provider()
        return provider.chat(messages)

    def _cleanup(self) -> None:
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def cleanup(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def reset_provider(self) -> None:
        self._provider = None
