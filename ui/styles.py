"""应用全局样式和 Fluent 主题配置。"""

from PyQt6.QtGui import QColor
from qfluentwidgets import Theme, setTheme, setThemeColor


# ── Fluent 主题配置 ──────────────────────────────────────────────
def apply_fluent_theme():
    """应用 Fluent Design 主题"""
    setTheme(Theme.LIGHT)
    setThemeColor(QColor("#4A90D9"))

# ── 颜色常量（保留用于自定义组件） ──────────────────────────────────────────────
COLOR_PRIMARY = "#4A90D9"
COLOR_PRIMARY_HOVER = "#357ABD"
COLOR_BG_SIDEBAR = "#F5F5F5"
COLOR_BG_CHAT = "#FFFFFF"
COLOR_BUBBLE_USER = "#4A90D9"
COLOR_BUBBLE_AI = "#F0F0F0"
COLOR_TEXT_USER = "#FFFFFF"
COLOR_TEXT_AI = "#333333"
COLOR_TEXT_SECONDARY = "#888888"
COLOR_BORDER = "#E0E0E0"
COLOR_DANGER = "#E74C3C"
COLOR_SUCCESS = "#27AE60"
COLOR_MEDIA_VIDEO = "#4A90D9"
COLOR_MEDIA_IMAGE = "#27AE60"
COLOR_MEDIA_AUDIO = "#E67E22"

# ── 按钮样式系统 ─────────────────────────────────────────────────
_BUTTON_RADIUS = 4

_BUTTON_SCHEMES = {
    "danger": {"bg": "#E81123", "hover": "#C50F1F", "pressed": "#A00D1A"},
    "save": {"bg": "#27AE60", "hover": "#219A52", "pressed": "#1E8449"},
    "generate": {"bg": "#E67E22", "hover": "#D35400", "pressed": "#BA4A00"},
}


def style_button(btn, category="default"):
    """Apply unified button style.

    Args:
        btn: A qfluentwidgets PushButton instance.
        category: One of "default", "danger", "save", "generate".
    """
    if category not in _BUTTON_SCHEMES:
        return
    c = _BUTTON_SCHEMES[category]
    has_icon = bool(btn.property("hasIcon")) or not btn.icon().isNull()
    left_pad = 36 if has_icon else 16
    btn.setStyleSheet(
        f"PushButton {{"
        f"  background-color: {c['bg']};"
        f"  color: white;"
        f"  border: none;"
        f"  border-radius: {_BUTTON_RADIUS}px;"
        f"  padding: 6px 16px 6px {left_pad}px;"
        f"}}"
        f"PushButton:hover {{"
        f"  background-color: {c['hover']};"
        f"}}"
        f"PushButton:pressed {{"
        f"  background-color: {c['pressed']};"
        f"}}"
        f"PushButton:disabled {{"
        f"  background-color: #CCCCCC;"
        f"  color: #888888;"
        f"}}"
    )
