from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.visual_style_model import VisualStyleListModel


class VisualStyleBridge(QObject):
    style_created = Signal(int)
    style_updated = Signal(int)
    style_deleted = Signal(int)

    def __init__(self, visual_style_service, parent=None):
        super().__init__(parent)
        self._visual_style_service = visual_style_service
        self._list_model = VisualStyleListModel(self)

    @Property(QObject, constant=True)
    def listModel(self):
        return self._list_model

    @Slot()
    def load_styles(self) -> None:
        styles = self._visual_style_service.list_styles()
        self._list_model.reset(styles)

    @Slot(str, str, result=int)
    def create_style(self, name: str, sample_image_path: str) -> int:
        try:
            style = self._visual_style_service.create_style(
                name=name,
                sample_image_path=sample_image_path,
            )
            self.load_styles()
            self.style_created.emit(style.id)
            return style.id
        except Exception as e:
            logger.error(f"创建风格失败: {e}")
            return -1

    @Slot(int, str, str)
    def update_style(self, style_id: int, name: str, sample_image_path: str) -> None:
        try:
            self._visual_style_service.update_style(
                style_id=style_id,
                name=name,
                sample_image_path=sample_image_path,
            )
            self.load_styles()
            self.style_updated.emit(style_id)
        except Exception as e:
            logger.error(f"更新风格失败: {e}")

    @Slot(int)
    def delete_style(self, style_id: int) -> None:
        try:
            self._visual_style_service.delete_style(style_id=style_id)
            self.load_styles()
            self.style_deleted.emit(style_id)
        except Exception as e:
            logger.error(f"删除风格失败: {e}")

    @Slot(int, result=str)
    def get_style_name(self, style_id: int) -> str:
        style = self._visual_style_service.get_style(style_id=style_id)
        return style.name if style else ""

    @Slot(int)
    def set_as_default(self, style_id: int) -> None:
        try:
            self._visual_style_service.set_default_style(style_id=style_id)
            self.load_styles()
        except Exception as e:
            logger.error(f"设置默认风格失败: {e}")

    @Slot(result=int)
    def get_default_style_id(self) -> int:
        style = self._visual_style_service.get_default_style()
        return style.id if style else -1
