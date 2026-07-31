import os
from pathlib import Path


def to_relative_path(absolute_path: str, workspace_root: str) -> str:
    if not absolute_path:
        return ""

    try:
        abs_path = Path(absolute_path).resolve()
        root_path = Path(workspace_root).resolve()

        if abs_path.is_relative_to(root_path):
            return str(abs_path.relative_to(root_path)).replace("\\", "/")
        else:
            raise ValueError(f"路径不在工作区内：{absolute_path}，工作区根目录：{workspace_root}")
    except (ValueError, OSError) as e:
        raise ValueError(f"无效的路径：{absolute_path}") from e


def to_absolute_path(relative_path: str, workspace_root: str) -> str:
    if not relative_path:
        return ""

    if os.path.isabs(relative_path):
        raise ValueError(f"数据库中存储了绝对路径，这是不允许的：{relative_path}。请删除数据库重新初始化。")

    return os.path.join(workspace_root, relative_path)


def normalize_path_for_storage(path: str, workspace_root: str) -> str:
    return to_relative_path(path, workspace_root)


def normalize_path_for_use(path: str, workspace_root: str) -> str:
    return to_absolute_path(path, workspace_root)
