"""项目列表模型，供 QML GridView/ListView 使用。"""

from __future__ import annotations

import os
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from models.project import Project
from utils.time_format import format_timestamp_short
from utils import paths


class ProjectListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    ResolutionRole = Qt.UserRole + 3
    RatioRole = Qt.UserRole + 4
    CoverPathRole = Qt.UserRole + 5
    CreatedAtRole = Qt.UserRole + 6

    _ROLE_NAMES = {
        IdRole: b"projectId",
        NameRole: b"name",
        ResolutionRole: b"resolution",
        RatioRole: b"aspectRatio",
        CoverPathRole: b"coverPath",
        CreatedAtRole: b"createdAt",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Project] = []
        # 获取 workspace 根目录（用于转换相对路径为绝对路径）
        workspace_root = paths.workspace_root()
        self._workspace_dir = paths.workspace_dir(workspace_root)

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
        if role == self.NameRole:
            return item.name
        if role == self.ResolutionRole:
            return item.resolution
        if role == self.RatioRole:
            return item.aspect_ratio
        if role == self.CoverPathRole:
            # 将相对路径转换为绝对路径
            if item.cover_image:
                abs_path = os.path.join(self._workspace_dir, item.cover_image)
                # 使用正斜杠（QML 兼容）
                return abs_path.replace('\\', '/')
            return ""
        if role == self.CreatedAtRole:
            return format_timestamp_short(item.created_at)
        return None

    def reset(self, projects: list[Project]) -> None:
        self.beginResetModel()
        self._data = list(projects)
        self.endResetModel()

    def add(self, project: Project) -> None:
        pos = len(self._data)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._data.append(project)
        self.endInsertRows()

    def remove_by_id(self, project_id: int) -> None:
        for i, p in enumerate(self._data):
            if p.id == project_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._data.pop(i)
                self.endRemoveRows()
                return
