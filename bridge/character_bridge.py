from __future__ import annotations

import json
from datetime import datetime
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.character_model import CharacterListModel
from bridge.workers import CharacterDesignImageWorker, OptimizeWorker


class CharacterBridge(QObject):
    data_changed = Signal()
    design_image_ready = Signal(str, str)  # char_uuid, image_path
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    characters_generated = Signal(int)  # count
    characters_optimized = Signal(int)  # count
    isOptimizingChanged = Signal()
    error = Signal(str)

    def __init__(self, character_service, text_model_service, image_service,
                 story_outline_service, screenplay_service, parent=None):
        super().__init__(parent)
        self._character_service = character_service
        self._text_model_service = text_model_service
        self._image_service = image_service
        self._story_outline_service = story_outline_service
        self._screenplay_service = screenplay_service
        self._model = CharacterListModel(self)
        self._workers = []
        self._optimizing = False

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(bool, notify=isOptimizingChanged)
    def isOptimizing(self):
        return self._optimizing

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

    @Slot(str, int)
    def optimize_with_ai(self, user_input: str, project_id: int) -> None:
        """AI 优化角色：自动判断生成或优化"""
        if self._optimizing:
            return

        try:
            # 1. 获取大纲和剧本
            outline = self._story_outline_service.get_or_create_story_outline(project_id)
            scenes = self._screenplay_service.list_scenes(project_id)

            if not outline.content.strip() or not scenes:
                self.error.emit("必须先完成大纲和剧本")
                return

            # 2. 查询现有角色
            characters = self._character_service.list_characters(project_id)

            # 3. 判断分支
            if not characters:
                self._generate_characters(outline.content, scenes, user_input, project_id)
            else:
                self._optimize_characters(outline.content, scenes, characters, user_input, project_id)

        except Exception as e:
            logger.exception("AI 优化角色失败")
            self.error.emit(str(e))

    def _generate_characters(self, outline_content: str, scenes: list, user_input: str, project_id: int) -> None:
        """生成模式：从大纲和剧本生成角色"""
        self._optimizing = True
        self.isOptimizingChanged.emit()

        script_content = self._format_script_as_text(scenes)

        worker = OptimizeWorker(self._text_model_service, [])
        worker._service = self._text_model_service
        worker._outline = outline_content
        worker._script = script_content
        worker._requirement = user_input

        def do_work():
            try:
                characters = worker._service.generate_characters(
                    worker._outline,
                    worker._script,
                    worker._requirement,
                )
                return characters
            except Exception as e:
                raise e

        worker.run = lambda: worker.finished.emit(do_work())

        def on_finished(characters: list) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            try:
                # 保存角色
                for char_data in characters:
                    self._character_service.create_character(
                        project_id=project_id,
                        name=char_data["name"],
                        ref_code=char_data["ref_code"],
                        description=char_data["description"],
                    )

                self.load_for_project(project_id)
                self.characters_generated.emit(len(characters))

            except Exception as e:
                logger.exception("保存生成的角色失败")
                self.error.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.error.emit(f"生成角色失败：{err}")

        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _optimize_characters(self, outline_content: str, scenes: list, characters: list, user_input: str, project_id: int) -> None:
        """优化模式：优化现有角色"""
        self._optimizing = True
        self.isOptimizingChanged.emit()

        script_content = self._format_script_as_text(scenes)
        current_characters = self._format_characters_as_text(characters)

        worker = OptimizeWorker(self._text_model_service, [])
        worker._service = self._text_model_service
        worker._outline = outline_content
        worker._script = script_content
        worker._current = current_characters
        worker._requirement = user_input

        def do_work():
            try:
                characters = worker._service.optimize_characters(
                    worker._outline,
                    worker._script,
                    worker._current,
                    worker._requirement,
                )
                return characters
            except Exception as e:
                raise e

        worker.run = lambda: worker.finished.emit(do_work())

        def on_finished(new_characters: list) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            try:
                # 删除旧角色
                for char in characters:
                    self._character_service.delete_character(char.id)

                # 保存新角色
                for char_data in new_characters:
                    self._character_service.create_character(
                        project_id=project_id,
                        name=char_data["name"],
                        ref_code=char_data["ref_code"],
                        description=char_data["description"],
                    )

                self.load_for_project(project_id)
                self.characters_optimized.emit(len(new_characters))

            except Exception as e:
                logger.exception("保存优化后的角色失败")
                self.error.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.error.emit(f"优化角色失败：{err}")

        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _format_script_as_text(self, scenes: list) -> str:
        """将场次列表格式化为文本"""
        from models.enums import SceneLocation, SceneTime

        lines = []
        for scene in scenes:
            location_type_str = {
                SceneLocation.INTERIOR: "内景",
                SceneLocation.EXTERIOR: "外景",
                SceneLocation.INTERIOR_EXTERIOR: "内景/外景",
            }.get(scene.location_type, "内景")

            time_type_str = {
                SceneTime.DAY: "日",
                SceneTime.NIGHT: "夜",
                SceneTime.DAWN: "晨",
                SceneTime.DUSK: "黄昏",
                SceneTime.EVENING: "傍晚",
                SceneTime.CUSTOM: scene.time_detail,
            }.get(scene.time_type, "日")

            lines.append(f"第{scene.scene_number}场 {location_type_str} {scene.location} {time_type_str}")
            lines.append(scene.content)
            lines.append("")

        return "\n".join(lines)

    def _format_characters_as_text(self, characters: list) -> str:
        """将角色列表格式化为文本"""
        lines = []
        for char in characters:
            lines.append(f"【{char.name}】（引用代号：{char.ref_code}）")
            lines.append(char.description)
            lines.append("")

        return "\n".join(lines)
