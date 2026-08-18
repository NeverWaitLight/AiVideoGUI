import os
import shutil
from pathlib import Path
from loguru import logger


def copy_resources_to_workspace(workspace_root: str) -> None:
    """将项目 resources 文件夹复制到系统工作目录

    Args:
        workspace_root: 工作区根目录（%LOCALAPPDATA%\\ai-video-gui）
    """
    project_resources = Path(__file__).parent.parent / "resources"
    workspace_resources = Path(workspace_root) / "resources"

    if not project_resources.exists():
        logger.warning(f"项目 resources 文件夹不存在: {project_resources}")
        return

    workspace_resources.mkdir(parents=True, exist_ok=True)

    root_files = ["settings.json"]

    for filename in root_files:
        src_file = project_resources / filename
        if not src_file.is_file():
            logger.debug(f"跳过不存在的根目录文件: {src_file}")
            continue

        dst_file = workspace_resources / filename
        if dst_file.exists():
            src_mtime = src_file.stat().st_mtime
            dst_mtime = dst_file.stat().st_mtime
            if src_mtime <= dst_mtime:
                continue
            logger.debug(f"更新资源文件: {filename}")
        else:
            logger.debug(f"复制资源文件: {filename}")

        shutil.copy2(src_file, dst_file)

    legacy_providers = workspace_resources / "providers.json"
    if legacy_providers.is_file():
        try:
            legacy_providers.unlink()
            logger.debug("已移除旧版 providers.json")
        except OSError as e:
            logger.warning(f"移除旧版 providers.json 失败: {e}")

    subdirs = ["styles", "covers"]

    for subdir in subdirs:
        src_dir = project_resources / subdir
        dst_dir = workspace_resources / subdir

        if not src_dir.exists():
            logger.debug(f"跳过不存在的子目录: {src_dir}")
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)

        for item in src_dir.iterdir():
            if item.is_file():
                src_file = item
                dst_file = dst_dir / item.name

                if dst_file.exists():
                    src_mtime = src_file.stat().st_mtime
                    dst_mtime = dst_file.stat().st_mtime
                    if src_mtime <= dst_mtime:
                        continue
                    logger.debug(f"更新资源文件: {item.name}")
                else:
                    logger.debug(f"复制资源文件: {item.name}")

                shutil.copy2(src_file, dst_file)

    logger.info(f"资源文件已同步到: {workspace_resources}")


def get_resource_path(workspace_root: str, relative_path: str) -> str:
    """获取资源文件的绝对路径

    Args:
        workspace_root: 工作区根目录
        relative_path: 相对路径（如 "resources/styles/felt.png"）

    Returns:
        资源文件的绝对路径
    """
    return os.path.join(workspace_root, relative_path)
