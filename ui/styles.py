"""应用全局样式和颜色常量。"""

# ── 颜色常量 ──────────────────────────────────────────────
COLOR_PRIMARY = "#4A90D9"
COLOR_PRIMARY_HOVER = "#357ABD"
COLOR_BG_SIDEBAR = "#F5F5F5"
COLOR_BG_CHAT = "#FFFFFF"
COLOR_BG_INPUT = "#FFFFFF"
COLOR_BUBBLE_USER = "#4A90D9"
COLOR_BUBBLE_AI = "#F0F0F0"
COLOR_TEXT_USER = "#FFFFFF"
COLOR_TEXT_AI = "#333333"
COLOR_TEXT_SECONDARY = "#888888"
COLOR_BORDER = "#E0E0E0"
COLOR_DANGER = "#E74C3C"
COLOR_SUCCESS = "#27AE60"


MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #FFFFFF;
}
QSplitter::handle {
    background-color: #E0E0E0;
    width: 1px;
}
"""

SIDEBAR_STYLE = """
QWidget#sidebar {
    background-color: #F5F5F5;
    border-right: 1px solid #E0E0E0;
}
QPushButton#newConversationBtn {
    background-color: #4A90D9;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#newConversationBtn:hover {
    background-color: #357ABD;
}
QPushButton#settingsBtn {
    background-color: transparent;
    color: #666666;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton#settingsBtn:hover {
    background-color: #E8E8E8;
}
QListWidget#conversationList {
    background-color: #F5F5F5;
    border: none;
    outline: none;
}
QListWidget#conversationList::item {
    padding: 12px 16px;
    border-radius: 6px;
    margin: 2px 8px;
}
QListWidget#conversationList::item:selected {
    background-color: #E3EDF7;
    color: #333333;
}
QListWidget#conversationList::item:hover:!selected {
    background-color: #EAEAEA;
}
"""

CHAT_AREA_STYLE = """
QWidget#chatArea {
    background-color: #FFFFFF;
}
QLabel#headerTitle {
    font-size: 16px;
    font-weight: bold;
    color: #333333;
    padding: 8px 0;
}
QLabel#headerModel {
    font-size: 12px;
    color: #888888;
    padding: 0 0 8px 0;
}
QScrollArea#messageScroll {
    border: none;
    background-color: #FFFFFF;
}
QWidget#messageContainer {
    background-color: #FFFFFF;
}
QTextEdit#inputBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    background-color: #FFFFFF;
}
QTextEdit#inputBox:focus {
    border-color: #4A90D9;
}
QPushButton#sendBtn {
    background-color: #4A90D9;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton#sendBtn:hover {
    background-color: #357ABD;
}
QPushButton#sendBtn:disabled {
    background-color: #CCCCCC;
}
"""

SETTINGS_DIALOG_STYLE = """
QDialog {
    background-color: #FFFFFF;
}
QLabel {
    font-size: 13px;
    color: #333333;
}
QLineEdit {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #4A90D9;
}
QComboBox {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QPushButton {
    padding: 8px 20px;
    border-radius: 4px;
    font-size: 13px;
}
QPushButton#saveBtn {
    background-color: #4A90D9;
    color: white;
    border: none;
}
QPushButton#saveBtn:hover {
    background-color: #357ABD;
}
QPushButton#cancelBtn {
    background-color: transparent;
    color: #666666;
    border: 1px solid #E0E0E0;
}
QPushButton#cancelBtn:hover {
    background-color: #F0F0F0;
}
QPushButton#browseBtn {
    background-color: transparent;
    color: #4A90D9;
    border: 1px solid #4A90D9;
    padding: 6px 12px;
}
QPushButton#browseBtn:hover {
    background-color: #E3EDF7;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""
