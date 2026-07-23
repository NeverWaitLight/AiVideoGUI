"""工作区路径工具：集中管理所有目录解析逻辑。"""

import os


def workspace_root() -> str:
    """返回应用工作区根目录。"""
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(root, "ai-video-gui")


def data_dir(root: str) -> str:
    """软件数据目录（DB + 配置）。"""
    return os.path.join(root, "data")


def cache_dir(root: str) -> str:
    """临时缓存目录（下载中转）。"""
    return os.path.join(root, "cache")


def logs_dir(root: str) -> str:
    """日志目录。"""
    return os.path.join(root, "logs")


def workspace_dir(root: str) -> str:
    """媒体文件工作区目录。"""
    return os.path.join(root, "workspace")


def chat_dir(root: str) -> str:
    """非项目对话生成的文件目录。"""
    return os.path.join(root, "workspace", "chat")


def projects_dir(root: str) -> str:
    """项目文件根目录。"""
    return os.path.join(root, "workspace", "projects")


def project_dir(root: str, project_id: str) -> str:
    """单个项目的文件目录。"""
    return os.path.join(root, "workspace", "projects", project_id)


def thumbnail_dir(base_dir: str) -> str:
    """指定目录下的缩略图隐藏子目录。"""
    return os.path.join(base_dir, ".thumbnails")
