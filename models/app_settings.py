from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSettings:
    """应用设置"""
    default_provider: str = ""              # 默认视频生成供应商
    default_chat_provider: str = ""         # 默认对话模型供应商
    default_image_provider: str = ""        # 默认图片生成供应商
    workspace_dir: str = ""                 # 工作区目录路径
    color_scheme: str = "System"            # 配色方案（System/Light/Dark）
    ignored_update_version: str = ""        # 已忽略的更新版本
    close_window_action: str = ""          # 关闭窗口行为（""/minimize/quit）
    stale_task_timeout_hours: int = 4      # 未完成任务超时小时数
