from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Property, Qt, Signal

from models.storyboard import Storyboard
from utils.path_converter import to_absolute_path


class StoryboardListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    SceneNumberRole = Qt.UserRole + 2
    ShotNumberRole = Qt.UserRole + 3
    ShotSizeRole = Qt.UserRole + 4
    CameraMovementRole = Qt.UserRole + 5
    VisualContentRole = Qt.UserRole + 6
    DialogueRole = Qt.UserRole + 7
    DurationRole = Qt.UserRole + 8
    DesignImageRole = Qt.UserRole + 9
    SoundEffectRole = Qt.UserRole + 10
    NotesRole = Qt.UserRole + 11
    SceneIdRole = Qt.UserRole + 12

    _ROLE_NAMES = {
        IdRole: b"shotId",
        SceneNumberRole: b"sceneNumber",
        ShotNumberRole: b"shotNumber",
        ShotSizeRole: b"shotSize",
        CameraMovementRole: b"cameraMovement",
        VisualContentRole: b"visualContent",
        DialogueRole: b"dialogue",
        DurationRole: b"duration",
        DesignImageRole: b"designImagePath",
        SoundEffectRole: b"soundEffect",
        NotesRole: b"notes",
        SceneIdRole: b"sceneId",
    }

    count_changed = Signal()

    def __init__(self, workspace_root: str = "", parent=None):
        super().__init__(parent)
        self._data: list[Storyboard] = []
        self._workspace_root = workspace_root

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    @Property(int, notify=count_changed)
    def count(self):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        item = self._data[index.row()]
        if role == self.IdRole:
            return item.id
        if role == self.SceneNumberRole:
            return item.scene_number
        if role == self.ShotNumberRole:
            return item.shot_number
        if role == self.ShotSizeRole:
            return item.shot_size.value
        if role == self.CameraMovementRole:
            return item.camera_movement
        if role == self.VisualContentRole:
            return item.content
        if role == self.DialogueRole:
            return item.dialogue
        if role == self.DurationRole:
            return item.duration
        if role == self.DesignImageRole:
            return to_absolute_path(item.design_image, self._workspace_root) if item.design_image else ""
        if role == self.SoundEffectRole:
            return item.sound_effect
        if role == self.NotesRole:
            return item.notes
        if role == self.SceneIdRole:
            return item.scene_id
        return None

    def reset(self, shots: list[Storyboard]) -> None:
        self.beginResetModel()
        self._data = list(shots)
        self.endResetModel()
        self.count_changed.emit()

    def get_by_index(self, row: int) -> Storyboard | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_design_image(self, shot_id: int, image_path: str) -> None:
        for i, s in enumerate(self._data):
            if s.id == shot_id:
                s.design_image = image_path
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.DesignImageRole])
                return
