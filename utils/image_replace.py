from __future__ import annotations

import os
from pathlib import Path

from loguru import logger

from utils.path_converter import to_absolute_path, to_relative_path


def try_remove_workspace_file(workspace_root: str, relative_path: str) -> None:
    """删除工作区内的旧图片文件，路径无效或不在工作区内时跳过。"""
    if not relative_path or not workspace_root:
        return

    try:
        absolute_path = to_absolute_path(relative_path, workspace_root)
    except ValueError:
        logger.warning(f"跳过删除无效路径：{relative_path}")
        return

    if not absolute_path or not os.path.isfile(absolute_path):
        return

    try:
        abs_resolved = Path(absolute_path).resolve()
        root_resolved = Path(workspace_root).resolve()
        if not abs_resolved.is_relative_to(root_resolved):
            logger.warning(f"跳过删除工作区外文件：{absolute_path}")
            return
    except (ValueError, OSError) as e:
        logger.warning(f"跳过删除文件（路径校验失败）：{absolute_path}，{e}")
        return

    try:
        os.remove(absolute_path)
        logger.info(f"已删除旧图片：{relative_path}")
    except OSError as e:
        logger.warning(f"删除旧图片失败：{absolute_path}，{e}")


def normalize_relative_path(workspace_root: str, path: str) -> str:
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            return to_relative_path(path, workspace_root)
        except ValueError:
            return path.replace("\\", "/")
    return path.replace("\\", "/")


def replace_stored_image(workspace_root: str, old_relative: str, new_relative: str) -> None:
    """DB 已指向新路径后，若旧路径不同则删除旧文件。"""
    old_norm = normalize_relative_path(workspace_root, old_relative)
    new_norm = normalize_relative_path(workspace_root, new_relative)
    if not old_norm or old_norm == new_norm:
        return
    try_remove_workspace_file(workspace_root, old_norm)
