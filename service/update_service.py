"""更新检查服务"""

import os
import subprocess
import requests
from loguru import logger
from packaging import version
from typing import Optional, Dict, Any, Callable


class UpdateService:
    """GitHub Release 更新检查服务"""

    GITHUB_REPO = "NeverWaitLight/AiVideoGUI"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def __init__(self, current_version: str, workspace_root: str, config_manager=None):
        self.current_version = current_version
        self.workspace_root = workspace_root
        self._config_manager = config_manager

    def check_update(self) -> Optional[Dict[str, Any]]:
        """
        检查是否有新版本

        Returns:
            如果有新版本，返回包含以下键的字典：
            - version: 新版本号
            - download_url: 下载地址
            - release_notes: 发布说明
            - published_at: 发布时间
            如果没有新版本或检查失败，返回 None
        """
        try:
            logger.info(f"检查更新：当前版本 {self.current_version}")

            response = requests.get(
                self.GITHUB_API_URL,
                timeout=10,
                headers={"Accept": "application/vnd.github+json"}
            )
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data.get("tag_name", "").lstrip("v")

            if not latest_version:
                logger.warning("无法获取最新版本号")
                return None

            logger.info(f"最新版本：{latest_version}")

            # 检查是否被忽略
            if self._config_manager:
                ignored_version = self._config_manager.settings.ignored_update_version
                if ignored_version and version.parse(latest_version) <= version.parse(ignored_version):
                    logger.info(f"版本 {latest_version} 已被忽略（忽略版本：{ignored_version}）")
                    return None

            if version.parse(latest_version) > version.parse(self.current_version):
                assets = release_data.get("assets", [])
                windows_asset = None

                for asset in assets:
                    name = asset.get("name", "").lower()
                    if name.endswith(".exe") or "windows" in name or "win" in name:
                        windows_asset = asset
                        break

                download_url = windows_asset.get("browser_download_url") if windows_asset else release_data.get("html_url")

                return {
                    "version": latest_version,
                    "download_url": download_url,
                    "release_notes": release_data.get("body", ""),
                    "published_at": release_data.get("published_at", ""),
                    "html_url": release_data.get("html_url", "")
                }

            logger.info("当前已是最新版本")
            return None

        except requests.RequestException as e:
            logger.error(f"检查更新失败：{e}")
            return None
        except Exception as e:
            logger.error(f"检查更新时发生错误：{e}")
            return None

    def download_update(self, download_url: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
        """
        下载更新安装包

        Args:
            download_url: 下载地址
            progress_callback: 进度回调函数，参数为 (已下载字节数, 总字节数)

        Returns:
            下载成功返回本地文件路径，失败返回 None
        """
        try:
            logger.info(f"开始下载更新：{download_url}")

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            # 从 URL 中提取文件名
            filename = download_url.split("/")[-1]
            if not filename.endswith(".exe"):
                filename = f"AI-Video-GUI-Setup-{self.current_version}.exe"

            # 保存到工作目录的 updates 子目录
            updates_dir = os.path.join(self.workspace_root, "updates")
            os.makedirs(updates_dir, exist_ok=True)
            save_path = os.path.join(updates_dir, filename)

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_reported = 0
            report_threshold = max(total_size // 100, 102400)  # 最少每 100KB 或 1% 报告一次

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            if downloaded - last_reported >= report_threshold or downloaded == total_size:
                                progress_callback(downloaded, total_size)
                                last_reported = downloaded

            logger.info(f"更新下载完成：{save_path}")
            return save_path

        except requests.RequestException as e:
            logger.error(f"下载更新失败：{e}")
            return None
        except Exception as e:
            logger.error(f"下载更新时发生错误：{e}")
            return None

    def install_update(self, installer_path: str) -> bool:
        """
        启动安装程序

        Args:
            installer_path: 安装程序路径

        Returns:
            启动成功返回 True，失败返回 False
        """
        try:
            if not os.path.isfile(installer_path):
                logger.error(f"安装程序不存在：{installer_path}")
                return False

            logger.info(f"启动安装程序：{installer_path}")

            # 使用 subprocess.Popen 启动安装程序（不等待完成）
            subprocess.Popen([installer_path], shell=True)

            logger.info("安装程序已启动，应用即将退出")
            return True

        except Exception as e:
            logger.error(f"启动安装程序失败：{e}")
            return False

    def ignore_version(self, version_to_ignore: str) -> None:
        """
        忽略指定版本的更新

        Args:
            version_to_ignore: 要忽略的版本号
        """
        if not self._config_manager:
            logger.warning("无法保存忽略版本：ConfigManager 未设置")
            return

        logger.info(f"忽略更新版本：{version_to_ignore}")
        self._config_manager.update_settings(ignored_update_version=version_to_ignore)
