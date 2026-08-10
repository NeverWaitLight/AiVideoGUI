import os
import sys


def workspace_root() -> str:
    if os.environ.get("DEV_MODE") == "1":
        if getattr(sys, 'frozen', False):
            project_root = os.path.dirname(sys.executable)
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "dev_workspace")

    root = os.environ.get("LOCALAPPDATA")
    if not root:
        root = os.path.expanduser("~")
    return os.path.join(root, "ai-video-gui")


def data_dir(root: str) -> str:
    return os.path.join(root, "data")


def cache_dir(root: str) -> str:
    return os.path.join(root, "cache")


def logs_dir(root: str) -> str:
    return os.path.join(root, "logs")


def workspace_dir(root: str) -> str:
    return root


def projects_dir(root: str) -> str:
    return os.path.join(root, "projects")


def project_dir(root: str, project_id: int) -> str:
    return os.path.join(root, "projects", str(project_id))


def thumbnail_dir(base_dir: str) -> str:
    return os.path.join(base_dir, ".thumbnails")


def resources_dir(root: str) -> str:
    return os.path.join(root, "resources")
