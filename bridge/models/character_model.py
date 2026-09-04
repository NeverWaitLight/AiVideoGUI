from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Property, Qt, Signal

from models.character import Character
from utils.path_converter import to_absolute_path, to_relative_path


class CharacterListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    UuidRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3
    RefCodeRole = Qt.UserRole + 4
    DescriptionRole = Qt.UserRole + 5
    DesignImageRole = Qt.UserRole + 6
    VoiceToneRole = Qt.UserRole + 7
    VoiceReferenceFileRole = Qt.UserRole + 8
    DesignImageRevisionRole = Qt.UserRole + 9

    _ROLE_NAMES = {
        IdRole: b"characterId",
        UuidRole: b"characterUuid",
        NameRole: b"name",
        RefCodeRole: b"refCode",
        DescriptionRole: b"description",
        DesignImageRole: b"designImagePath",
        VoiceToneRole: b"voiceTone",
        VoiceReferenceFileRole: b"voiceReferenceFile",
        DesignImageRevisionRole: b"designImageRevision",
    }

    count_changed = Signal()

    def __init__(self, workspace_root: str, parent=None):
        super().__init__(parent)
        self._data: list[Character] = []
        self._workspace_root = workspace_root
        self._design_image_revision: dict[str, int] = {}

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
        if role == self.UuidRole:
            return item.uuid
        if role == self.NameRole:
            return item.name
        if role == self.RefCodeRole:
            return item.ref_code
        if role == self.DescriptionRole:
            return item.description
        if role == self.DesignImageRole:
            # 将相对路径转换为绝对路径供 QML 显示
            return to_absolute_path(item.design_image, self._workspace_root) if item.design_image else ""
        if role == self.DesignImageRevisionRole:
            return self._design_image_revision.get(item.uuid, 0)
        if role == self.VoiceToneRole:
            return item.voice_tone
        if role == self.VoiceReferenceFileRole:
            return to_absolute_path(item.voice_reference_file, self._workspace_root) if item.voice_reference_file else ""
        return None

    def reset(self, characters: list[Character]) -> None:
        self.beginResetModel()
        self._data = list(characters)
        self._design_image_revision.clear()
        self.endResetModel()
        self.count_changed.emit()

    def append(self, character: Character) -> None:
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(character)
        self.endInsertRows()
        self.count_changed.emit()

    def get_by_index(self, row: int) -> Character | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_design_image(self, char_uuid: str, image_path: str) -> None:
        for i, c in enumerate(self._data):
            if c.uuid == char_uuid:
                if image_path:
                    c.design_image = to_relative_path(image_path, self._workspace_root)
                else:
                    c.design_image = ""
                self._design_image_revision[char_uuid] = (
                    self._design_image_revision.get(char_uuid, 0) + 1
                )
                idx = self.index(i)
                self.dataChanged.emit(
                    idx,
                    idx,
                    [self.DesignImageRole, self.DesignImageRevisionRole],
                )
                return
