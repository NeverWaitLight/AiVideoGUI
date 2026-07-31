import os


def workspace_root() -> str:
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(root, "ai-video-gui")


def data_dir(root: str) -> str:
    return os.path.join(root, "data")


def cache_dir(root: str) -> str:
    return os.path.join(root, "cache")


def logs_dir(root: str) -> str:
    return os.path.join(root, "logs")


def workspace_dir(root: str) -> str:
    return os.path.join(root, "workspace")


def chat_dir(root: str) -> str:
    return os.path.join(root, "workspace", "chat")


def projects_dir(root: str) -> str:
    return os.path.join(root, "workspace", "projects")


def project_dir(root: str, project_id: int) -> str:
    return os.path.join(root, "workspace", "projects", str(project_id))


def thumbnail_dir(base_dir: str) -> str:
    return os.path.join(base_dir, ".thumbnails")
