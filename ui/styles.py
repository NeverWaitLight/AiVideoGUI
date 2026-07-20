"""应用全局样式和颜色常量。"""

# ── 颜色常量 ──────────────────────────────────────────────
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

MAIN_WINDOW_STYLE = """
QMainWindow { background-color: #FFFFFF; }
QSplitter::handle { background-color: #E0E0E0; width: 1px; }
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
    padding: 10px 0px;
    font-size: 13px;
    font-weight: bold;
    min-height: 20px;
}
QPushButton#newConversationBtn:hover { background-color: #357ABD; }
QPushButton#settingsBtn {
    background-color: transparent;
    color: #555555;
    border: 1px solid #D0D0D0;
    border-radius: 6px;
    padding: 10px 0px;
    font-size: 13px;
    min-height: 20px;
}
QPushButton#settingsBtn:hover {
    background-color: #E8E8E8;
    border-color: #BBBBBB;
}
QListWidget#conversationList {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#conversationList::item {
    padding: 2px 4px;
    border-radius: 6px;
    margin: 1px 0px;
}
QListWidget#conversationList::item:selected {
    background-color: #DDE8F4;
}
QListWidget#conversationList::item:hover:!selected { background-color: #EAEAEA; }
QPushButton#deleteConvBtn {
    background-color: transparent;
    color: #BBBBBB;
    border: none;
    border-radius: 11px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#deleteConvBtn:hover {
    background-color: #E74C3C;
    color: white;
}
"""

CHAT_AREA_STYLE = """
QWidget#chatArea { background-color: #FFFFFF; }
QWidget#chatHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E0E0E0;
}
QLabel#headerTitle { font-size: 15px; font-weight: bold; color: #333333; }
QLabel#headerModel { font-size: 12px; color: #999999; }
QScrollArea#messageScroll { border: none; background-color: #FFFFFF; }
QWidget#messageContainer { background-color: #FFFFFF; }
QWidget#inputArea {
    background-color: #FFFFFF;
    border-top: 1px solid #E0E0E0;
}
QTextEdit#inputBox {
    border: 1px solid #D0D0D0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    background-color: #FAFAFA;
}
QTextEdit#inputBox:focus {
    border-color: #4A90D9;
    background-color: #FFFFFF;
}
QPushButton#sendBtn {
    background-color: #4A90D9;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
    min-width: 72px;
    min-height: 38px;
}
QPushButton#sendBtn:hover { background-color: #357ABD; }
QPushButton#sendBtn:disabled { background-color: #CCCCCC; }
"""

SETTINGS_DIALOG_STYLE = """
QDialog { background-color: #FFFFFF; }
QLabel { font-size: 13px; color: #333333; }
QLineEdit {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QLineEdit:focus { border-color: #4A90D9; }
QComboBox {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QPushButton { padding: 8px 20px; border-radius: 4px; font-size: 13px; }
QPushButton#saveBtn {
    background-color: #4A90D9;
    color: white;
    border: none;
}
QPushButton#saveBtn:hover { background-color: #357ABD; }
QPushButton#cancelBtn {
    background-color: transparent;
    color: #666666;
    border: 1px solid #E0E0E0;
}
QPushButton#cancelBtn:hover { background-color: #F0F0F0; }
QPushButton#browseBtn {
    background-color: transparent;
    color: #4A90D9;
    border: 1px solid #4A90D9;
    padding: 6px 12px;
}
QPushButton#browseBtn:hover { background-color: #E3EDF7; }
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
