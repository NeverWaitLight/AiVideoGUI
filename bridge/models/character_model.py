from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from models.character import Character


class CharacterListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    UuidRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3
    RefCodeRole = Qt.UserRole + 4
    DescriptionRole = Qt.UserRole + 5
    DesignImageRole = Qt.UserRole + 6

    _ROLE_NAMES = {
        IdRole: b"characterId",
        UuidRole: b"characterUuid",
        NameRole: b"name",
        RefCodeRole: b"refCode",
        DescriptionRole: b"description",
        DesignImageRole: b"designImagePath",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Character] = []

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
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
            return item.design_image
        return None

    def reset(self, characters: list[Character]) -> None:
        self.beginResetModel()
        self._data = list(characters)
        self.endResetModel()

    def get_by_index(self, row: int) -> Character | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_design_image(self, char_uuid: str, image_path: str) -> None:
        for i, c in enumerate(self._data):
            if c.uuid == char_uuid:
                c.design_image = image_path
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.DesignImageRole])
                return
