"""视频生成 Provider 层。"""

from providers.base import VideoProvider
from providers.dashscope import DashScopeProvider

__all__ = ["VideoProvider", "DashScopeProvider"]
