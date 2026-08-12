from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.character_model import CharacterListModel
from bridge.workers import CharacterDesignImageWorker, CharacterRefineWorker, CharacterWorker


class CharacterBridge(QObject):
    data_changed = Signal()
    character_saved = Signal()
    design_image_ready = Signal(str, str)  # char_uuid, image_path
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    description_refined = Signal(str, str)  # char_uuid, new_description
    description_refine_failed = Signal(str)
    characters_generated = Signal(int)  # count
    characters_optimized = Signal(int)  # count
    isOptimizingChanged = Signal()
    bridge_error = Signal(str)

    def __init__(self, character_service, text_model_service, image_service,
                 story_outline_service, screenplay_service, project_service=None, visual_style_service=None,
                 container=None, parent=None):
        super().__init__(parent)
        self._character_service = character_service
        self._text_model_service = text_model_service
        self._image_service = image_service
        self._story_outline_service = story_outline_service
        self._screenplay_service = screenplay_service
        self._project_service = project_service
        self._visual_style_service = visual_style_service
        self._container = container

        # 获取 workspace_root
        workspace_root = container.config.workspace_root() if container else ""
        self._model = CharacterListModel(workspace_root=workspace_root, parent=self)

        self._workers = []
        self._optimizing = False
        self._character_worker = None
        self._project_id: int = -1

    def _get_project_name(self, project_id: int | None = None) -> str | None:
        pid = project_id if project_id is not None else self._project_id
        if self._project_service and pid >= 0:
            project = self._project_service.get_project(project_id=pid)
            return project.name if project else None
        return None

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(bool, notify=isOptimizingChanged)
    def isOptimizing(self):
        return self._optimizing

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        self._project_id = project_id
        chars = self._character_service.list_characters(project_id=project_id)
        self._model.reset(chars)

    @Slot(int, str, str, str, str, str)
    def create_character(self, project_id: int, name: str, ref_code: str, description: str, voice_tone: str = "", voice_reference_file: str = "") -> None:
        self._character_service.create_character(
            project_id=project_id, name=name, ref_code=ref_code, description=description,
            voice_tone=voice_tone, voice_reference_file=voice_reference_file,
        )
        self.load_for_project(project_id)
        self.data_changed.emit()
        self.character_saved.emit()

    @Slot(int, str, str, str, str, str)
    def save_new_character(self, project_id: int, name: str, ref_code: str, description: str, voice_tone: str = "", voice_reference_file: str = "") -> None:
        if not name.strip():
            self.bridge_error.emit("请输入角色名")
            return
        self._character_service.create_character(
            project_id=project_id, name=name.strip(), ref_code=ref_code.strip(), description=description.strip(),
            voice_tone=voice_tone.strip(), voice_reference_file=voice_reference_file.strip(),
        )
        self.load_for_project(project_id)
        self.data_changed.emit()
        self.character_saved.emit()

    @Slot(str, str, str, str, str, str)
    def save_existing_character(self, char_uuid: str, name: str, ref_code: str, description: str, voice_tone: str = "", voice_reference_file: str = "") -> None:
        if not name.strip():
            self.bridge_error.emit("请输入角色名")
            return
        self._character_service.update_character(
            character_uuid=char_uuid, name=name.strip(), ref_code=ref_code.strip(), description=description.strip(),
            voice_tone=voice_tone.strip(), voice_reference_file=voice_reference_file.strip(),
        )
        self.data_changed.emit()
        self.character_saved.emit()

    @Slot(str, str, str, str, str, str)
    def update_character(self, char_uuid: str, name: str, ref_code: str, description: str, voice_tone: str = "", voice_reference_file: str = "") -> None:
        self._character_service.update_character(
            character_uuid=char_uuid, name=name, ref_code=ref_code, description=description,
            voice_tone=voice_tone, voice_reference_file=voice_reference_file,
        )
        self.data_changed.emit()

    @Slot(str)
    def delete_character(self, char_uuid: str) -> None:
        self._character_service.delete_character(character_uuid=char_uuid)
        self.data_changed.emit()

    @Slot(str, int, str)
    def generate_design_image(self, char_uuid: str, project_id: int, user_requirement: str = "") -> None:
        try:
            chars = self._character_service.list_characters(project_id=project_id)
            character = None
            for c in chars:
                if c.uuid == char_uuid:
                    character = c
                    break
            if not character:
                self.design_image_failed.emit("角色不存在")
                return

            visual_style = ""
            if self._project_service and self._visual_style_service:
                project = self._project_service.get_project(project_id=project_id)
                if project and project.visual_style_id:
                    style = self._visual_style_service.get_style(project.visual_style_id)
                    if style:
                        visual_style = style.name

            workspace_root = None
            if hasattr(self, '_container') and self._container:
                workspace_root = self._container.config.workspace_root()

            worker = CharacterDesignImageWorker(
                text_service=self._text_model_service, image_service=self._image_service,
                character_service=self._character_service, character=character, project_id=project_id,
                user_requirement=user_requirement, visual_style=visual_style,
                project_name=self._get_project_name(project_id),
                config_manager=self._container.config_manager() if hasattr(self, '_container') else None,
                session_manager=self._container.session_manager() if hasattr(self, '_container') else None,
                workspace_root=workspace_root,
            )
            worker.finished.connect(lambda path: self._on_design_done(char_uuid, path))
            worker.failed.connect(self.design_image_failed.emit)
            worker.progress_update.connect(self.design_image_progress.emit)
            worker.finished.connect(worker.deleteLater)
            worker.failed.connect(worker.deleteLater)
            worker.start()
            self._workers.append(worker)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.design_image_failed.emit(error_msg)

    def _on_design_done(self, char_uuid: str, path: str) -> None:
        # Worker 内部已经保存到数据库，这里只需更新 Model 和发出信号
        # path 是相对路径，需要转换为绝对路径供模型使用
        from utils.path_converter import to_absolute_path
        workspace_root = self._container.config.workspace_root() if self._container else ""
        absolute_path = to_absolute_path(path, workspace_root)

        self._model.update_design_image(char_uuid, absolute_path)
        self.design_image_ready.emit(char_uuid, absolute_path)

    @Slot(str, str, str)
    def refine_description(self, char_uuid: str, current_description: str, user_requirement: str) -> None:
        try:
            character_name = ""
            for c in self._model._data:
                if c.uuid == char_uuid:
                    character_name = c.name
                    break

            if not character_name:
                self.description_refine_failed.emit("角色不存在")
                return

            worker = CharacterRefineWorker(
                text_service=self._text_model_service,
                character_name=character_name,
                current_description=current_description,
                user_requirement=user_requirement,
                project_id=self._project_id if self._project_id >= 0 else None,
                project_name=self._get_project_name(),
            )
            worker.finished.connect(lambda desc: self._on_refine_done(char_uuid, desc))
            worker.failed.connect(self.description_refine_failed.emit)
            worker.finished.connect(worker.deleteLater)
            worker.failed.connect(worker.deleteLater)
            worker.start()
            self._workers.append(worker)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.description_refine_failed.emit(error_msg)

    def _on_refine_done(self, char_uuid: str, new_description: str) -> None:
        self.description_refined.emit(char_uuid, new_description)

    @Slot(str, result=str)
    def get_history(self, char_uuid: str) -> str:
        try:
            history = self._character_service.list_history(character_uuid=char_uuid)
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
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(list)
    def batch_delete(self, char_ids: list) -> None:
        for cid in char_ids:
            try:
                self._character_service.delete_character(character_uuid=cid)
            except Exception:
                pass
        self.data_changed.emit()

    @Slot(result=str)
    def get_all_ids(self) -> str:
        ids = [c.uuid for c in self._model._data]
        return json.dumps(ids)

    @Slot(str, int)
    def optimize_with_ai(self, user_input: str, project_id: int) -> None:
        """AI 优化角色：自动判断生成或优化"""
        if self._optimizing:
            return

        try:
            # 1. 获取大纲和剧本
            outline = self._story_outline_service.get_or_create_story_outline(project_id=project_id)
            scenes = self._screenplay_service.list_scenes(project_id=project_id)

            if not outline.content.strip() or not scenes:
                self.bridge_error.emit("必须先完成大纲和剧本")
                return

            # 2. 查询现有角色
            characters = self._character_service.list_characters(project_id=project_id)

            # 3. 判断分支
            if not characters:
                self._generate_characters(outline.content, scenes, user_input, project_id)
            else:
                self._optimize_characters(outline.content, scenes, characters, user_input, project_id)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    def _generate_characters(self, outline_content: str, scenes: list, user_input: str, project_id: int) -> None:
        self._optimizing = True
        self.isOptimizingChanged.emit()

        script_content = self._format_script_as_text(scenes)

        self._character_worker = CharacterWorker(
            text_service=self._text_model_service,
            mode='generate',
            project_id=project_id,
            project_name=self._get_project_name(project_id),
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_input,
        )

        def on_finished(characters: list) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            try:
                for char_data in characters:
                    self._character_service.create_character(
                        project_id=project_id,
                        name=char_data["name"],
                        ref_code=char_data["ref_code"],
                        description=char_data["description"],
                        voice_tone=char_data.get("voice_tone", ""),
                    )

                self.load_for_project(project_id)
                self.characters_generated.emit(len(characters))

            except Exception as e:
                self.bridge_error.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.bridge_error.emit(f"生成角色失败：{err}")

        self._character_worker.finished.connect(on_finished)
        self._character_worker.failed.connect(on_failed)
        self._character_worker.finished.connect(self._character_worker.deleteLater)
        self._character_worker.start()

    def _optimize_characters(self, outline_content: str, scenes: list, characters: list, user_input: str, project_id: int) -> None:
        self._optimizing = True
        self.isOptimizingChanged.emit()

        script_content = self._format_script_as_text(scenes)
        current_characters = self._format_characters_as_text(characters)

        self._character_worker = CharacterWorker(
            text_service=self._text_model_service,
            mode='optimize',
            project_id=project_id,
            project_name=self._get_project_name(project_id),
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_input,
        )

        def on_finished(new_characters: list) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            try:
                for char in characters:
                    self._character_service.delete_character(character_uuid=char.id)

                for char_data in new_characters:
                    self._character_service.create_character(
                        project_id=project_id,
                        name=char_data["name"],
                        ref_code=char_data["ref_code"],
                        description=char_data["description"],
                        voice_tone=char_data.get("voice_tone", ""),
                    )

                self.load_for_project(project_id)
                self.characters_optimized.emit(len(new_characters))

            except Exception as e:
                self.bridge_error.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.bridge_error.emit(f"优化角色失败：{err}")

        self._character_worker.finished.connect(on_finished)
        self._character_worker.failed.connect(on_failed)
        self._character_worker.finished.connect(self._character_worker.deleteLater)
        self._character_worker.start()

    def _format_script_as_text(self, scenes: list) -> str:
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
        lines = []
        for char in characters:
            lines.append(f"【{char.name}】（引用代号：{char.ref_code}）")
            lines.append(char.description)
            lines.append("")

        return "\n".join(lines)
