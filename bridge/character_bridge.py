from __future__ import annotations

import json
from datetime import datetime
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.character_model import CharacterListModel
from bridge.workers import CharacterDesignImageWorker


class CharacterBridge(QObject):
    data_changed = Signal()
    design_image_ready = Signal(str, str)  # char_uuid, image_path
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    error = Signal(str)

    def __init__(self, character_service, text_model_service, image_service, parent=None):
        super().__init__(parent)
        self._character_service = character_service
        self._text_model_service = text_model_service
        self._image_service = image_service
        self._model = CharacterListModel(self)
        self._workers = []

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        chars = self._character_service.list_characters(project_id)
        self._model.reset(chars)

    @Slot(int, str, str, str)
    def create_character(self, project_id: int, name: str, ref_code: str, description: str) -> None:
        self._character_service.create_character(
            project_id=project_id, name=name, ref_code=ref_code, description=description,
        )
        self.load_for_project(project_id)
        self.data_changed.emit()

    @Slot(int, str, str, str)
    def update_character(self, char_id: int, name: str, ref_code: str, description: str) -> None:
        self._character_service.update_character(
            character_id=char_id, name=name, ref_code=ref_code, description=description,
        )
        self.data_changed.emit()

    @Slot(int)
    def delete_character(self, char_id: int) -> None:
        self._character_service.delete_character(char_id)
        self.data_changed.emit()

    @Slot(str, result=str)
    def extract_traits(self, description: str) -> str:
        return self._character_service.extract_fixed_traits(description)

    @Slot(str, int)
    def generate_design_image(self, char_uuid: str, project_id: int) -> None:
        chars = self._character_service.list_characters(project_id)
        character = None
        for c in chars:
            if c.uuid == char_uuid:
                character = c
                break
        if not character:
            return

        worker = CharacterDesignImageWorker(
            self._text_model_service, self._image_service,
            self._character_service, character, project_id,
        )
        worker.finished.connect(lambda path: self._on_design_done(char_uuid, path))
        worker.failed.connect(self.design_image_failed.emit)
        worker.progress_update.connect(self.design_image_progress.emit)
        worker.start()
        self._workers.append(worker)

    def _on_design_done(self, char_uuid: str, path: str) -> None:
        self._model.update_design_image(char_uuid, path)
        self.design_image_ready.emit(char_uuid, path)

    @Slot(str, result=str)
    def get_history(self, char_uuid: str) -> str:
        try:
            history = self._character_service.list_history(char_uuid)
            result = []
            for h in history:
                result.append({
                    "name": h.name,
                    "refCode": h.ref_code,
                    "description": h.description,
                    "createdAt": h.created_at,
                    "displayTime": datetime.fromtimestamp(h.created_at / 1000).strftime("%Y-%m-%d %H:%M"),
                })
            return json.dumps(result)
        except Exception as e:
            logger.exception("获取角色历史失败")
            return "[]"

    @Slot(str, str)
    def upload_design_image(self, char_uuid: str, image_path: str) -> None:
        try:
            self._character_service.update_character(
                character_uuid=char_uuid, design_image=image_path,
            )
            self._model.update_design_image(char_uuid, image_path)
            self.design_image_ready.emit(char_uuid, image_path)
        except Exception as e:
            logger.exception("上传角色设计图失败")
            self.error.emit(str(e))

    @Slot(list)
    def batch_delete(self, char_ids: list) -> None:
        for cid in char_ids:
            try:
                self._character_service.delete_character(cid)
            except Exception as e:
                logger.error(f"删除角色 {cid} 失败: {e}")
        self.data_changed.emit()

    @Slot(result=str)
    def get_all_ids(self) -> str:
        ids = [c.id for c in self._model._data]
        return json.dumps(ids)
