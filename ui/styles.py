"""应用全局样式和 Fluent 主题配置。"""

from qfluentwidgets import Theme, setTheme, setThemeColor
from PyQt6.QtGui import QColor

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
