from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.conversation_model import ConversationListModel
from bridge.models.message_model import MessageListModel
from models.enums import MessageStatus
from storage.repositories.conversation_repository import ConversationRepository
from storage.repositories.message_repository import MessageRepository
from storage.repositories.media_repository import MediaRepository


def format_time_short(dt) -> str:
    from datetime import datetime
    if not isinstance(dt, datetime):
        return str(dt)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")


class ConversationBridge(QObject):
    conversation_created = Signal(str)
    message_added = Signal(str, str, str)  # msg_id, role, content
    conversation_list_changed = Signal()

    def __init__(self, video_service, chat_service, session_manager, parent=None):
        super().__init__(parent)
        self._video_service = video_service
        self._chat_service = chat_service
        self._session_manager = session_manager
        self._current_conv_id: str | None = None
        self._model = ConversationListModel(self)
        self._messages = MessageListModel(self)

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(QObject, constant=True)
    def messages(self):
        return self._messages

    @Slot()
    def load_all(self) -> None:
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        convs = conv_repo.list_all(is_hidden=False)
        non_project = [c for c in convs if not c.project_id]
        self._model.reset(non_project)

    @Slot()
    def create_new(self) -> None:
        conv = self._video_service.create_conversation(
            provider_name="dashscope", model_name="wan2.7-t2v",
            title="新对话",
        )
        self._model.add(conv, at_top=True)
        self._current_conv_id = conv.id
        self._messages.reset([])
        self.conversation_created.emit(conv.id)

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        convs = conv_repo.list_by_project(project_id, is_hidden=False)
        self._model.reset(convs)

    @Slot(int)
    def create_for_project(self, project_id: int) -> None:
        conv = self._video_service.create_conversation(
            provider_name="dashscope", model_name="wan2.7-t2v",
            title="新对话", project_id=str(project_id),
        )
        self._model.add(conv, at_top=True)
        self._current_conv_id = conv.id
        self._messages.reset([])
        self.conversation_created.emit(conv.id)

    @Slot(str)
    def select(self, conv_id: str) -> None:
        self._current_conv_id = conv_id
        self._load_messages(conv_id)

    @Slot(str)
    def delete(self, conv_id: str) -> None:
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        self._session_manager.begin_write()
        try:
            conv_repo.delete(conv_id)
            self._session_manager.commit_write()
        except Exception:
            self._session_manager.rollback_write()
            raise
        self._model.remove_by_id(conv_id)
        if self._current_conv_id == conv_id:
            self._current_conv_id = None
            self._messages.reset([])
        self.conversation_list_changed.emit()

    @Slot(str, str, str, str, str, int, bool, bool)
    def send_message(self, text: str, provider: str, model: str,
                     resolution: str, ratio: str, duration: int = 5,
                     prompt_extend: bool = True, watermark: bool = False) -> None:
        if not text.strip():
            return
        if not self._current_conv_id:
            conv = self._video_service.create_conversation(
                provider_name=provider, model_name=model,
                title="新对话",
            )
            self._model.add(conv, at_top=True)
            self._current_conv_id = conv.id
            self._messages.reset([])
            self.conversation_created.emit(conv.id)
        user_msg = self._video_service.add_user_message(self._current_conv_id, text)
        self._messages.append(user_msg)
        self.message_added.emit(user_msg.id, "user", text)
        from bridge.workers import ChatWorker
        worker = ChatWorker(self._chat_service, self._current_conv_id, text, self)
        worker.reply_ready.connect(self._on_chat_reply)
        worker.reply_failed.connect(self._on_chat_failed)
        worker.start()
        self._chat_service.generate_title(self._current_conv_id, text)

    def _on_chat_reply(self, conv_id: str, reply: str) -> None:
        if conv_id != self._current_conv_id:
            return
        assistant_msg = self._video_service.add_assistant_message(conv_id, reply)
        self._messages.append(assistant_msg)
        self.message_added.emit(assistant_msg.id, "assistant", reply)

    def _on_chat_failed(self, conv_id: str, error: str) -> None:
        if conv_id != self._current_conv_id:
            return
        logger.error(f"对话回复失败: {error}")
        error_msg = self._video_service.add_assistant_message(conv_id, f"[错误] {error}")
        self._messages.append(error_msg)
        self.message_added.emit(error_msg.id, "assistant", f"[错误] {error}")

    @Slot(str, str)
    def update_title(self, conv_id: str, title: str) -> None:
        self._model.update_title(conv_id, title)

    @Slot(str)
    def update_status(self, msg_id: str, status: str) -> None:
        self._messages.update_status(msg_id, status)

    @Slot(str, str)
    def set_completed(self, msg_id: str, local_path: str) -> None:
        self._messages.update_status(msg_id, "completed", local_path=local_path)

    @Slot(str, str)
    def set_failed(self, msg_id: str, error: str) -> None:
        self._messages.update_status(msg_id, "failed", error=error)

    def _load_messages(self, conv_id: str) -> None:
        msg_repo = self._session_manager.get_repo(MessageRepository)
        media_repo = self._session_manager.get_repo(MediaRepository)

        msgs = msg_repo.list_by_conversation(conv_id)
        meta = {}
        for msg in msgs:
            if msg.role == "assistant" and msg.status == MessageStatus.COMPLETED:
                media_file = media_repo.get_by_message_id(msg.id)
                if media_file:
                    meta[msg.id] = {
                        "duration": media_file.duration,
                        "width": media_file.width,
                        "height": media_file.height,
                    }
        self._messages.reset(msgs, meta)
