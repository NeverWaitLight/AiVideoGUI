"""大纲编辑器：支持编辑和历史版本管理。"""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QDialog,
    QDialogButtonBox,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ToolButton,
    FluentIcon,
    CardWidget,
    ComboBox,
    ProgressRing,
)

from models.data_models import Outline, OutlineHistory
from service.outline_service import OutlineService
from service.text_model_service import TextModelService

logger = logging.getLogger(__name__)


class OptimizeWorker(QThread):
    """AI 优化后台线程。"""

    finished = pyqtSignal(str)  # 优化后的内容
    failed = pyqtSignal(str)  # 错误消息

    def __init__(
        self,
        text_service: TextModelService,
        original_content: str,
        requirement: str,
        model: str,
    ):
        super().__init__()
        self._service = text_service
        self._original = original_content
        self._requirement = requirement
        self._model = model

    def run(self) -> None:
        try:
            result = self._service.optimize_outline(
                self._original, self._requirement, self._model
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("AI 优化失败")
            self.failed.emit(str(e))


class AIOptimizeDialog(QDialog):
    """AI 优化大纲对话框。"""

    def __init__(
        self,
        current_content: str,
        text_service: TextModelService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._current_content = current_content
        self._text_service = text_service
        self._optimized_content = ""
        self._worker: OptimizeWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("AI 优化大纲")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 当前大纲预览
        preview_label = QLabel("当前大纲内容")
        preview_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setPlainText(self._current_content)
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background: #F8F8F8;
                color: #666;
            }
            """
        )
        layout.addWidget(self.preview_text)

        # 模型选择
        model_label = QLabel("选择模型")
        model_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(model_label)

        self.model_combo = ComboBox()
        self.model_combo.addItems([
            "qwen-max (通义千问旗舰版)",
            "qwen-plus (通义千问增强版)",
            "qwen-turbo (通义千问极速版)",
        ])
        self.model_combo.setCurrentIndex(0)
        layout.addWidget(self.model_combo)

        # 优化要求输入
        req_label = QLabel("优化要求")
        req_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(req_label)

        self.requirement_text = QTextEdit()
        self.requirement_text.setPlaceholderText(
            "请输入对大纲的优化要求，例如：\n"
            "- 增加更多细节描述\n"
            "- 调整结构使其更有逻辑性\n"
            "- 添加时间线规划\n"
            "- 补充角色设定部分"
        )
        self.requirement_text.setMinimumHeight(120)
        self.requirement_text.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
            """
        )
        layout.addWidget(self.requirement_text)

        # 加载状态
        self.loading_widget = QWidget()
        loading_layout = QHBoxLayout(self.loading_widget)
        loading_layout.setContentsMargins(0, 8, 0, 8)
        loading_layout.setSpacing(12)

        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(24, 24)
        self.progress_ring.hide()
        loading_layout.addWidget(self.progress_ring)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 13px; color: #666;")
        loading_layout.addWidget(self.status_label, stretch=1)

        layout.addWidget(self.loading_widget)

        # 按钮
        button_box = QDialogButtonBox()
        self.optimize_btn = button_box.addButton("开始优化", QDialogButtonBox.ButtonRole.AcceptRole)
        self.optimize_btn.setObjectName("primaryButton")
        cancel_btn = button_box.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)

        button_box.accepted.connect(self._on_optimize)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _on_optimize(self) -> None:
        """开始优化。"""
        requirement = self.requirement_text.toPlainText().strip()
        if not requirement:
            QMessageBox.warning(self, "提示", "请输入优化要求")
            return

        # 解析模型名称
        model_text = self.model_combo.currentText()
        model = model_text.split(" ")[0]  # 提取 "qwen-max" 部分

        # 禁用输入
        self.requirement_text.setEnabled(False)
        self.model_combo.setEnabled(False)
        self.optimize_btn.setEnabled(False)

        # 显示加载状态
        self.progress_ring.show()
        self.status_label.setText("正在调用 AI 模型优化大纲...")

        # 启动后台线程
        self._worker = OptimizeWorker(
            self._text_service, self._current_content, requirement, model
        )
        self._worker.finished.connect(self._on_optimize_success)
        self._worker.failed.connect(self._on_optimize_failed)
        self._worker.start()

    def _on_optimize_success(self, optimized_content: str) -> None:
        """优化成功。"""
        self._optimized_content = optimized_content
        self.progress_ring.hide()
        self.status_label.setText("")
        self.accept()

    def _on_optimize_failed(self, error_msg: str) -> None:
        """优化失败。"""
        self.progress_ring.hide()
        self.status_label.setText("")

        # 恢复输入
        self.requirement_text.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.optimize_btn.setEnabled(True)

        QMessageBox.critical(self, "优化失败", f"AI 优化失败：{error_msg}")

    def get_optimized_content(self) -> str:
        """获取优化后的内容。"""
        return self._optimized_content


class HistoryListItem(QWidget):
    """历史版本列表项。"""

    restore_clicked = pyqtSignal(str)  # history_id

    def __init__(self, history: OutlineHistory, parent: QWidget | None = None):
        super().__init__(parent)
        self._history = history
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 时间标签
        time_label = QLabel(self._history.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        time_label.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(time_label, stretch=1)

        # 恢复按钮
        restore_btn = PushButton("恢复")
        restore_btn.setFixedHeight(28)
        restore_btn.clicked.connect(lambda: self.restore_clicked.emit(self._history.id))
        layout.addWidget(restore_btn)


class OutlineEditor(QWidget):
    """大纲编辑器页面。"""

    back_clicked = pyqtSignal()
    next_step_clicked = pyqtSignal(str)  # outline_content

    def __init__(
        self,
        outline_service: OutlineService,
        text_service: TextModelService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._service = outline_service
        self._text_service = text_service
        self._current_outline: Outline | None = None
        self._current_project_id: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet("background: white; border-bottom: 1px solid #E0E0E0;")
        toolbar.setFixedHeight(60)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 12, 20, 12)
        toolbar_layout.setSpacing(12)

        # 返回按钮
        back_btn = ToolButton(FluentIcon.RETURN)
        back_btn.setFixedSize(36, 36)
        back_btn.setIconSize(QSize(18, 18))
        back_btn.setToolTip("返回项目详情")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        toolbar_layout.addWidget(back_btn)

        # 标题
        title_label = QLabel("大纲编辑")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        toolbar_layout.addWidget(title_label, stretch=1)

        # AI 优化按钮
        self.ai_optimize_btn = PushButton("AI 优化")
        self.ai_optimize_btn.setIcon(FluentIcon.ROBOT)
        self.ai_optimize_btn.setFixedHeight(36)
        self.ai_optimize_btn.clicked.connect(self._on_ai_optimize)
        toolbar_layout.addWidget(self.ai_optimize_btn)

        # 保存按钮
        self.save_btn = PrimaryPushButton("保存")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._on_save)
        toolbar_layout.addWidget(self.save_btn)

        # 下一步按钮
        self.next_btn = PrimaryPushButton("下一步")
        self.next_btn.setIcon(FluentIcon.RIGHT_ARROW)
        self.next_btn.setFixedHeight(36)
        self.next_btn.clicked.connect(self._on_next_step)
        toolbar_layout.addWidget(self.next_btn)

        layout.addWidget(toolbar)

        # 主内容区域：左侧编辑器 + 右侧历史版本
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：编辑器
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(12)

        # 编辑器标题
        editor_title = QLabel("大纲内容")
        editor_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        editor_layout.addWidget(editor_title)

        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入项目大纲...")
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
                background: white;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
            """
        )
        editor_layout.addWidget(self.text_edit, stretch=1)

        # 右侧：历史版本
        history_widget = QWidget()
        history_widget.setFixedWidth(320)
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(20, 20, 20, 20)
        history_layout.setSpacing(12)

        # 历史版本标题
        history_title = QLabel("历史版本")
        history_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        history_layout.addWidget(history_title)

        # 历史版本列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #F0F0F0;
                padding: 0px;
            }
            QListWidget::item:hover {
                background: #F5F5F5;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
            }
            """
        )
        history_layout.addWidget(self.history_list, stretch=1)

        splitter.addWidget(editor_widget)
        splitter.addWidget(history_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 320])

        layout.addWidget(splitter, stretch=1)

    def load_outline(self, project_id: str) -> None:
        """加载项目大纲。"""
        self._current_project_id = project_id
        self._current_outline = self._service.get_or_create_outline(project_id)

        # 加载大纲内容
        self.text_edit.setPlainText(self._current_outline.content)

        # 加载历史版本
        self._load_history()

    def _load_history(self) -> None:
        """加载历史版本列表。"""
        self.history_list.clear()

        if not self._current_outline:
            return

        history_list = self._service.list_history(self._current_outline.id)

        if not history_list:
            # 显示空状态
            empty_item = QListWidgetItem(self.history_list)
            empty_widget = QLabel("暂无历史版本")
            empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_widget.setStyleSheet("color: #999; padding: 20px;")
            empty_item.setSizeHint(empty_widget.sizeHint())
            self.history_list.addItem(empty_item)
            self.history_list.setItemWidget(empty_item, empty_widget)
            return

        for history in history_list:
            item = QListWidgetItem(self.history_list)
            widget = HistoryListItem(history)
            widget.restore_clicked.connect(self._on_restore)
            item.setSizeHint(widget.sizeHint())
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, widget)

    def _on_save(self) -> None:
        """保存大纲。"""
        if not self._current_outline:
            return

        content = self.text_edit.toPlainText().strip()

        # 检查内容是否有变化
        if content == self._current_outline.content:
            QMessageBox.information(self, "提示", "内容未发生变化")
            return

        try:
            self._service.update_outline(self._current_outline.id, content)
            self._current_outline.content = content
            self._current_outline.updated_at = datetime.now()

            # 重新加载历史版本
            self._load_history()

            QMessageBox.information(self, "成功", "大纲已保存")
            logger.info(f"保存大纲：{self._current_outline.id}")

        except Exception as e:
            logger.exception("保存大纲失败")
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _on_restore(self, history_id: str) -> None:
        """恢复历史版本。"""
        if not self._current_outline:
            return

        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复到此历史版本吗？当前内容将被保存为新的历史版本。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.restore_from_history(self._current_outline.id, history_id)

            # 重新加载大纲
            if self._current_project_id:
                self.load_outline(self._current_project_id)

            QMessageBox.information(self, "成功", "已恢复到历史版本")
            logger.info(f"恢复大纲历史版本：{history_id}")

        except Exception as e:
            logger.exception("恢复历史版本失败")
            QMessageBox.critical(self, "错误", f"恢复失败：{e}")

    def _on_ai_optimize(self) -> None:
        """AI 优化大纲。"""
        if not self._current_outline:
            return

        current_content = self.text_edit.toPlainText()

        # 显示优化对话框
        dialog = AIOptimizeDialog(current_content, self._text_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            optimized_content = dialog.get_optimized_content()
            if optimized_content:
                # 将优化后的内容填入编辑器
                self.text_edit.setPlainText(optimized_content)
                QMessageBox.information(
                    self, "成功", "AI 优化完成，内容已更新到编辑器。记得保存哦！"
                )
                logger.info("AI 优化大纲成功")

    def _on_next_step(self) -> None:
        """下一步：生成剧本。"""
        if not self._current_outline:
            return

        # 检查大纲是否已保存
        current_content = self.text_edit.toPlainText().strip()
        if current_content != self._current_outline.content:
            reply = QMessageBox.question(
                self,
                "提示",
                "检测到大纲内容有变化，是否先保存大纲再继续？",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # 保存大纲
                try:
                    self._service.update_outline(self._current_outline.id, current_content)
                    self._current_outline.content = current_content
                    self._current_outline.updated_at = datetime.now()
                    logger.info(f"保存大纲：{self._current_outline.id}")
                except Exception as e:
                    logger.exception("保存大纲失败")
                    QMessageBox.critical(self, "错误", f"保存失败：{e}")
                    return

        # 发射信号，传递大纲内容
        self.next_step_clicked.emit(current_content)
