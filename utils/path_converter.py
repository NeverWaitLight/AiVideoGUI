import os
from pathlib import Path, PurePosixPath


def to_relative_path(absolute_path: str, workspace_root: str) -> str:
    if not absolute_path:
        return ""

    try:
        abs_path = Path(absolute_path).resolve()
        root_path = Path(workspace_root).resolve()

        if abs_path.is_relative_to(root_path):
            rel = abs_path.relative_to(root_path)
            return str(PurePosixPath(*rel.parts))
        else:
            raise ValueError(f"路径不在工作区内：{absolute_path}，工作区根目录：{workspace_root}")
    except (ValueError, OSError) as e:
        raise ValueError(f"无效的路径：{absolute_path}") from e


def to_absolute_path(relative_path: str, workspace_root: str) -> str:
    if not relative_path:
        return ""

    if os.path.isabs(relative_path):
        try:
            return to_absolute_path(
                to_relative_path(relative_path, workspace_root),
                workspace_root,
            )
        except ValueError:
            return relative_path

    return os.path.join(workspace_root, relative_path)


def normalize_path_for_storage(path: str, workspace_root: str) -> str:
    return to_relative_path(path, workspace_root)


def normalize_path_for_use(path: str, workspace_root: str) -> str:
    return to_absolute_path(path, workspace_root)


def to_qml_local_path(path: str) -> str:
    """将本地绝对路径转为 QML file URL 可用的正斜杠形式"""
    if not path:
        return ""
    return path.replace("\\", "/")
