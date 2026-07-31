"""路径转换工具：相对路径与绝对路径互转。

用于数据库存储：所有文件路径以相对于 workspace_root 的相对路径存储，
以便工作区目录迁移时无需修改数据库。

注意：不兼容旧的绝对路径格式，所有路径必须是相对路径。
"""

import os
from pathlib import Path


def to_relative_path(absolute_path: str, workspace_root: str) -> str:
    """将绝对路径转换为相对于 workspace_root 的相对路径。

    Args:
        absolute_path: 绝对路径（如 C:/Users/admin/.../workspace/projects/1/video.mp4）
        workspace_root: 工作区根目录（如 C:/Users/admin/.../ai-video-gui）

    Returns:
        相对路径（如 workspace/projects/1/video.mp4）
        如果路径不在 workspace_root 下，抛出异常

    Raises:
        ValueError: 如果路径不在 workspace_root 下
    """
    if not absolute_path:
        return ""

    try:
        abs_path = Path(absolute_path).resolve()
        root_path = Path(workspace_root).resolve()

        # 检查是否在 workspace_root 下
        if abs_path.is_relative_to(root_path):
            return str(abs_path.relative_to(root_path)).replace("\\", "/")
        else:
            # 不在工作区下，抛出异常
            raise ValueError(f"路径不在工作区内：{absolute_path}，工作区根目录：{workspace_root}")
    except (ValueError, OSError) as e:
        raise ValueError(f"无效的路径：{absolute_path}") from e


def to_absolute_path(relative_path: str, workspace_root: str) -> str:
    """将相对路径转换为绝对路径。

    Args:
        relative_path: 相对路径（如 workspace/projects/1/video.mp4）
        workspace_root: 工作区根目录（如 C:/Users/admin/.../ai-video-gui）

    Returns:
        绝对路径（如 C:/Users/admin/.../workspace/projects/1/video.mp4）

    Raises:
        ValueError: 如果输入是绝对路径（不兼容旧格式）
    """
    if not relative_path:
        return ""

    # 不兼容旧的绝对路径格式
    if os.path.isabs(relative_path):
        raise ValueError(f"数据库中存储了绝对路径，这是不允许的：{relative_path}。请删除数据库重新初始化。")

    # 拼接为绝对路径
    return os.path.join(workspace_root, relative_path)


def normalize_path_for_storage(path: str, workspace_root: str) -> str:
    """标准化路径用于存储（转换为相对路径）。

    这是 to_relative_path 的别名，语义更清晰。
    """
    return to_relative_path(path, workspace_root)


def normalize_path_for_use(path: str, workspace_root: str) -> str:
    """标准化路径用于使用（转换为绝对路径）。

    这是 to_absolute_path 的别名，语义更清晰。
    """
    return to_absolute_path(path, workspace_root)
