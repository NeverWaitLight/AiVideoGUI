"""注册 Windows AppUserModelID，使 Toast 能进入通知中心并保留历史。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from loguru import logger

APP_AUMID = "Waitlight.AiVideoGUI"
APP_DISPLAY_NAME = "AiVideoGUI"


def resolve_app_icon_path() -> Path | None:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "resources" / "logo.ico")
        candidates.append(Path(sys.executable).resolve().parent / "resources" / "logo.ico")
    else:
        candidates.append(Path(__file__).resolve().parent.parent / "resources" / "logo.ico")

    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "ai-video-gui" / "resources" / "logo.ico")

    for path in candidates:
        if path.is_file():
            return path
    return None


def ensure_stable_icon_path(icon_path: Path | None = None) -> Path | None:
    """把图标复制到用户工作区，供注册表 IconUri 长期引用。"""
    src = icon_path or resolve_app_icon_path()
    if src is None or not src.is_file():
        return None

    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return src.resolve()

    dst = Path(local) / "ai-video-gui" / "resources" / "logo.ico"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
        return dst.resolve()
    except OSError as e:
        logger.warning(f"复制通知图标失败，改用原路径：{e}")
        return src.resolve()


def register_aumid(display_name: str = APP_DISPLAY_NAME, icon_path: Path | None = None) -> None:
    import winreg

    stable_icon = ensure_stable_icon_path(icon_path)
    key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{APP_AUMID}"
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, display_name)
        if stable_icon is not None:
            winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, str(stable_icon))


def set_current_process_aumid(aumid: str = APP_AUMID) -> None:
    import ctypes

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str(aumid))
    except Exception as e:
        logger.warning(f"设置进程 AppUserModelID 失败：{e}")


def ensure_start_menu_shortcut(
    display_name: str = APP_DISPLAY_NAME,
    icon_path: Path | None = None,
) -> None:
    """创建开始菜单快捷方式，便于系统把通知归到本应用。"""
    try:
        programs = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        programs.mkdir(parents=True, exist_ok=True)
        lnk_path = programs / f"{display_name}.lnk"

        if getattr(sys, "frozen", False):
            target = str(Path(sys.executable).resolve())
            arguments = ""
            workdir = str(Path(sys.executable).resolve().parent)
        else:
            target = str(Path(sys.executable).resolve())
            main_py = Path(__file__).resolve().parent.parent / "main.py"
            arguments = f'"{main_py}"'
            workdir = str(main_py.parent)

        icon = ensure_stable_icon_path(icon_path)
        icon_location = f"{icon},0" if icon else f"{target},0"

        def _ps_escape(value: str) -> str:
            return value.replace("'", "''")

        script = f"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut('{_ps_escape(str(lnk_path))}')
$sc.TargetPath = '{_ps_escape(target)}'
$sc.Arguments = '{_ps_escape(arguments)}'
$sc.WorkingDirectory = '{_ps_escape(workdir)}'
$sc.IconLocation = '{_ps_escape(icon_location)}'
$sc.Description = '{_ps_escape(display_name)}'
$sc.Save()
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"创建开始菜单快捷方式失败：{result.stderr.strip() or result.stdout.strip()}")
    except Exception as e:
        logger.warning(f"创建开始菜单快捷方式失败（不影响 Toast 发送）：{e}")


def ensure_windows_toast_identity(display_name: str = APP_DISPLAY_NAME) -> str:
    """启动时调用：注册 AUMID、设置进程身份、补齐开始菜单快捷方式。"""
    if sys.platform != "win32":
        return APP_AUMID
    try:
        set_current_process_aumid(APP_AUMID)
        register_aumid(display_name=display_name)
        ensure_start_menu_shortcut(display_name=display_name)
        logger.info(f"已注册 Windows Toast 身份：{APP_AUMID}")
    except Exception as e:
        logger.warning(f"注册 Windows Toast 身份失败：{e}")
    return APP_AUMID
