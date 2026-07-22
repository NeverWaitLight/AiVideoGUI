"""主窗口：组装 UI 与 VideoService，编排完整生成链路。"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QWidget,
    QMainWindow,
    QDialog,
    QVBoxLayout,
    QLabel,
)

from config.manager import ConfigManager
from service.chat_service import ChatService
from service.media_service import MediaService
from service.outline_service import OutlineService
from service.project_service import ProjectService
from service.script_service import ScriptService
from service.shot_service import ShotService
from service.task_polling_service import TaskPollingService
from service.text_model_service import TextModelService
from service.video_service import VideoService, _PROVIDER_REGISTRY
from storage.database import DatabaseManager
from ui.chat_area import ChatArea
from ui.media_library import MediaLibrary
from ui.outline_editor import OutlineEditor
from ui.project_detail_page import ProjectDetailPage
from ui.project_grid_page import ProjectGridPage
from ui.project_page import ProjectPage
from ui.script_editor import ScriptEditor
from ui.settings_dialog import SettingsDialog
from ui.shot_editor import ShotEditor
from ui.sidebar import Sidebar
from ui.styles import apply_fluent_theme
from ui.tab_bar import TabBar
from ui.widgets import VideoStatusCard

logger = logging.getLogger(__name__)


def _format_time(dt: datetime) -> str:
    """将 datetime 格式化为显示时间（今天 HH:MM，其他 MM-DD HH:MM）。"""
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")


def _app_data_dir() -> str:
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(root, "ai-video-gui")


class _BatchGenerationController(QObject):
    """批量串行生成控制器：逐个提交任务，等待完成后再提交下一个。"""

    progress = pyqtSignal(int, int, int, int, str)  # index, total, scene, shot, status
    all_done = pyqtSignal(int, int)  # success_count, failed_count
    terminated = pyqtSignal(int, int)  # success_count, failed_count

    def __init__(
        self,
        shot_list: list[dict],
        service: VideoService,
        polling_service: TaskPollingService,
        provider_name: str,
        model_name: str,
        project,
        provider_cfg,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._shot_list = shot_list
        self._service = service
        self._polling = polling_service
        self._provider_name = provider_name
        self._model_name = model_name
        self._project = project
        self._provider_cfg = provider_cfg
        self._index = 0
        self._success = 0
        self._failed = 0
        self._current_message_id: str | None = None
        self._stopped = False

    def start(self) -> None:
        self._stopped = False
        self._polling.task_finished.connect(self._on_task_finished)
        self._polling.task_failed.connect(self._on_task_failed)
        self._submit_next()

    def stop(self) -> None:
        """停止继续提交新任务，当前任务仍会在后台轮询完成。"""
        if self._stopped:
            return
        self._stopped = True
        self.progress.emit(self._index, len(self._shot_list), 0, 0, "正在停止...")
        logger.info("批量生成已收到停止请求，当前任务完成后不再继续")

    def _cleanup_and_terminate(self) -> None:
        """断开轮询信号并通知 UI 终止。"""
        try:
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.terminated.emit(self._success, self._failed)

    def _submit_next(self) -> None:
        if self._stopped:
            self._cleanup_and_terminate()
            return
        if self._index >= len(self._shot_list):
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
            self.all_done.emit(self._success, self._failed)
            return

        shot = self._shot_list[self._index]
        scene_number = shot["scene_number"]
        shot_number = shot["shot_number"]
        prompt = shot["prompt"]
        project_id = shot["project_id"]

        self.progress.emit(self._index, len(self._shot_list), scene_number, shot_number, "正在提交任务...")

        try:
            conv_title = f"分镜视频-场{scene_number}镜{shot_number}"
            conv = self._service.create_conversation(
                self._provider_name, self._model_name, conv_title,
                project_id=project_id, is_hidden=True,
            )

            params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
            params["resolution"] = self._project.resolution
            params["ratio"] = self._project.aspect_ratio

            msg = self._service.submit_task(
                conversation_id=conv.id,
                prompt=prompt,
                provider_name=self._provider_name,
                params=params,
            )
            self._current_message_id = msg.task_id
            self.progress.emit(self._index, len(self._shot_list), scene_number, shot_number, f"任务已提交，等待生成... (task: {msg.task_id[:12]}...)")
            logger.info(f"批量生成 [{self._index + 1}/{len(self._shot_list)}] 场{scene_number}镜{shot_number} 已提交 task_id={msg.task_id}")

        except Exception as e:
            logger.exception(f"批量生成提交失败：场{scene_number}镜{shot_number}")
            self._failed += 1
            self._index += 1
            self.progress.emit(self._index - 1, len(self._shot_list), scene_number, shot_number, f"提交失败：{e}")
            if self._stopped:
                self._cleanup_and_terminate()
                return
            self._submit_next()

    def _on_task_finished(self, message_id: str, local_path: str) -> None:
        msg = self._service._db.get_message(message_id)
        if not msg or msg.task_id != self._current_message_id:
            return

        shot = self._shot_list[self._index]
        self._success += 1
        self._index += 1
        self.progress.emit(
            self._index - 1, len(self._shot_list),
            shot["scene_number"], shot["shot_number"], "已完成"
        )
        logger.info(f"批量生成 [{self._index}/{len(self._shot_list)}] 场{shot['scene_number']}镜{shot['shot_number']} 完成")
        if self._stopped:
            self._cleanup_and_terminate()
            return
        self._submit_next()

    def _on_task_failed(self, message_id: str, error: str) -> None:
        msg = self._service._db.get_message(message_id)
        if not msg or msg.task_id != self._current_message_id:
            return

        shot = self._shot_list[self._index]
        self._failed += 1
        self._index += 1
        self.progress.emit(
            self._index - 1, len(self._shot_list),
            shot["scene_number"], shot["shot_number"], f"失败：{error}"
        )
        logger.warning(f"批量生成 [{self._index}/{len(self._shot_list)}] 场{shot['scene_number']}镜{shot['shot_number']} 失败：{error}")
        if self._stopped:
            self._cleanup_and_terminate()
            return
        self._submit_next()


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 视频生成")
        self.setMinimumSize(960, 640)
        self.resize(1100, 700)

        # 应用 Fluent 主题
        apply_fluent_theme()

        self._current_conversation_id: str | None = None
        self._video_cards: dict[str, VideoStatusCard] = {}
        self._current_mode: int = 0  # 0: 直接生成, 1: 项目管理
        self._current_project_id: str | None = None

        # ── 初始化基础设施 ──
        data_dir = _app_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        self._db = DatabaseManager(os.path.join(data_dir, "ai-video-gui.db"))
        self._config = ConfigManager(os.path.join(data_dir, "config.json"))

        # VideoService 仅负责对话和任务提交
        self._service = VideoService(self._db, self._config)
        self._chat_service = ChatService(self._config)

        # 项目服务
        self._project_service = ProjectService(self._db)

        # 大纲服务
        self._outline_service = OutlineService(self._db)

        # 剧本服务
        self._script_service = ScriptService(self._db)

        # 分镜服务
        self._shot_service = ShotService(self._db)

        # 文本模型服务
        self._text_model_service = TextModelService(self._config)

        # 素材库服务
        download_dir = self._config.settings.default_download_dir or self._default_download_dir()
        self._media_service = MediaService(self._db, download_dir)

        # 全局任务轮询服务
        temp_dir = self._default_temp_dir()
        self._polling_service = TaskPollingService(
            db=self._db,
            config=self._config,
            download_dir=download_dir,
            temp_dir=temp_dir,
            provider_registry=_PROVIDER_REGISTRY,
        )
        self._polling_service.set_media_service(self._media_service)

        self._setup_ui()
        self._connect_signals()
        self._load_conversations()

        # 启动全局轮询服务
        self._polling_service.start()

    @staticmethod
    def _default_download_dir() -> str:
        home = os.path.expanduser("~")
        return os.path.join(home, "Videos", "AI-Video-GUI")

    @staticmethod
    def _default_temp_dir() -> str:
        return os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "ai-video-gui")

    # ───────── UI 组装 ─────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab 栏（最左侧）
        self.tab_bar = TabBar()
        main_layout.addWidget(self.tab_bar)

        # 直接生成模式的内容
        self.direct_mode_widget = self._create_direct_mode()
        main_layout.addWidget(self.direct_mode_widget)

        # 项目管理模式的内容
        self.project_mode_widget = self._create_project_mode()
        main_layout.addWidget(self.project_mode_widget)
        self.project_mode_widget.hide()

    def _create_direct_mode(self) -> QWidget:
        """创建直接生成模式的 UI。"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar()

        # 右侧内容区域
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_area = ChatArea()
        self.media_library = MediaLibrary(
            self._media_service,
            on_play=self._play_video,
            on_open_folder=self._open_folder,
        )

        # 初始显示聊天区域
        content_layout.addWidget(self.chat_area)
        self.chat_area.show()
        content_layout.addWidget(self.media_library)
        self.media_library.hide()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 860])

        layout.addWidget(splitter)
        return widget

    def _create_project_mode(self) -> QWidget:
        """创建项目管理模式的 UI（三层导航：网格 → 详情 → 模块）。"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 第一层：项目网格页面（初始视图）
        self.project_grid_page = ProjectGridPage(self._project_service)
        layout.addWidget(self.project_grid_page)

        # 第二层：项目详情页面（模块入口）
        self.project_detail_page = ProjectDetailPage(self._project_service)
        layout.addWidget(self.project_detail_page)
        self.project_detail_page.hide()

        # 第三层：项目素材库
        self.project_media_library = MediaLibrary(
            self._media_service,
            on_play=self._play_video,
            on_open_folder=self._open_folder,
        )
        layout.addWidget(self.project_media_library)
        self.project_media_library.hide()

        # 第三层：大纲编辑器
        self.outline_editor = OutlineEditor(self._outline_service, self._text_model_service)
        layout.addWidget(self.outline_editor)
        self.outline_editor.hide()

        # 第三层：剧本编辑器
        self.script_editor = ScriptEditor(self._script_service)
        layout.addWidget(self.script_editor)
        self.script_editor.hide()

        # 第三层：分镜编辑器
        self.shot_editor = ShotEditor(self._shot_service, self._script_service)
        layout.addWidget(self.shot_editor)
        self.shot_editor.hide()

        # 第三层：项目对话界面（三栏布局：项目列表 + 对话列表 + 聊天区域）
        self.project_conversation_widget = QWidget()
        conv_layout = QHBoxLayout(self.project_conversation_widget)
        conv_layout.setContentsMargins(0, 0, 0, 0)
        conv_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 项目页面（左侧项目列表 + 中间对话列表）
        self.project_page = ProjectPage(self._project_service)

        # 右侧聊天区域（复用 ChatArea）
        self.project_chat_area = ChatArea()

        splitter.addWidget(self.project_page)
        splitter.addWidget(self.project_chat_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([480, 620])

        conv_layout.addWidget(splitter)
        layout.addWidget(self.project_conversation_widget)
        self.project_conversation_widget.hide()

        return widget

    def _connect_signals(self) -> None:
        # Tab 栏信号
        self.tab_bar.tab_changed.connect(self._on_tab_changed)

        # 项目网格页面信号
        self.project_grid_page.project_selected.connect(self._on_project_grid_selected)

        # 项目详情页面信号
        self.project_detail_page.module_selected.connect(self._on_project_module_selected)
        self.project_detail_page.back_clicked.connect(self._on_project_detail_back)

        # 项目素材库信号
        self.project_media_library.back_clicked.connect(self._on_project_media_back)

        # 大纲编辑器信号
        self.outline_editor.back_clicked.connect(self._on_outline_editor_back)
        self.outline_editor.next_step_clicked.connect(self._on_outline_next_step)

        # 剧本编辑器信号
        self.script_editor.back_clicked.connect(self._on_script_editor_back)
        self.script_editor.generate_storyboard_clicked.connect(self._on_generate_storyboard)

        # 分镜编辑器信号
        self.shot_editor.back_clicked.connect(self._on_shot_editor_back)
        self.shot_editor.video_generation_requested.connect(self._on_shot_video_generation)
        self.shot_editor.batch_video_generation_requested.connect(self._on_batch_video_generation)

        # 直接生成模式信号
        self.sidebar.new_conversation_clicked.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.conversation_deleted.connect(self._on_conversation_deleted)
        self.sidebar.library_clicked.connect(self._on_library)
        self.sidebar.settings_clicked.connect(self._on_settings)
        self.chat_area.message_sent.connect(self._on_message_sent)

        # 项目管理模式信号
        self.project_page.new_conversation_clicked.connect(self._on_project_new_conversation)
        self.project_page.conversation_selected.connect(self._on_project_conversation_selected)
        self.project_page.conversation_deleted.connect(self._on_project_conversation_deleted)
        self.project_chat_area.message_sent.connect(self._on_project_message_sent)

        # 连接素材库信号
        self.media_library.jump_to_conversation_requested.connect(self._on_jump_to_conversation)

        # 连接全局轮询服务信号
        self._polling_service.status_changed.connect(self._on_status_changed)
        self._polling_service.download_progress.connect(self._on_download_progress)
        self._polling_service.task_finished.connect(self._on_task_finished)
        self._polling_service.task_failed.connect(self._on_task_failed)

        self._chat_service.title_ready.connect(self._on_title_ready)

    # ───────── 数据加载 ─────────

    def _load_conversations(self) -> None:
        convs = self._db.list_conversations()
        # 只加载没有项目关联的对话到侧边栏（直接生成模式）
        for conv in convs:
            if not conv.project_id:
                time_text = conv.created_at.strftime("%Y-%m-%d %H:%M")
                self.sidebar.add_conversation(conv.id, conv.title, time_text, at_top=False)

        # 找到最新的非项目对话
        non_project_convs = [c for c in convs if not c.project_id]
        if non_project_convs:
            latest = non_project_convs[0]
            self.sidebar.select_conversation(latest.id)
            self._on_conversation_selected(latest.id)

        # 加载项目列表
        self.project_page.load_projects()

    def _load_messages(self, conversation_id: str) -> None:
        self.chat_area.clear_messages()
        for msg in self._db.list_messages(conversation_id):
            time_str = _format_time(msg.created_at)
            if msg.role == "user":
                self.chat_area.add_user_message(msg.content, time_str)
            else:
                card = self.chat_area.add_video_card(
                    message_text=msg.content, timestamp=time_str
                )
                self._video_cards[msg.id] = card
                card.open_folder_clicked.connect(self._open_folder)
                if msg.status.value == "completed" and msg.local_path:
                    meta = self._db.get_video_metadata_by_message(msg.id) or {}
                    card.set_completed(
                        msg.local_path,
                        duration=meta.get("duration", 0),
                        width=meta.get("width", 0),
                        height=meta.get("height", 0),
                    )
                    card.play_btn.clicked.connect(lambda _, p=msg.local_path: self._play_video(p))
                elif msg.status.value == "failed":
                    card.set_failed("生成失败")
                else:
                    card.set_generating()
        QTimer.singleShot(0, self.chat_area._scroll_to_bottom)

    # ───────── Tab 切换 ─────────

    def _on_tab_changed(self, index: int) -> None:
        """Tab 切换事件。"""
        self._current_mode = index
        if index == 0:
            # 切换到直接生成模式
            self.project_mode_widget.hide()
            self.direct_mode_widget.show()
        else:
            # 切换到项目管理模式
            self.direct_mode_widget.hide()
            self.project_mode_widget.show()
            # 显示网格页面，隐藏其他页面
            self.project_grid_page.show()
            self.project_detail_page.hide()
            self.project_media_library.hide()
            self.outline_editor.hide()
            self.project_conversation_widget.hide()
            self.project_grid_page.load_projects()

    def _on_project_grid_selected(self, project_id: str) -> None:
        """从网格页面点击项目，进入详情页面。"""
        self._current_project_id = project_id
        # 隐藏网格页面，显示详情页面
        self.project_grid_page.hide()
        self.project_detail_page.show()
        self.project_detail_page.set_project(project_id)

    def _on_project_module_selected(self, project_id: str, module_name: str) -> None:
        """项目模块被选中。"""
        self._current_project_id = project_id

        if module_name == "outline":
            # 进入大纲编辑器
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.project_media_library.hide()
            self.script_editor.hide()
            self.outline_editor.show()
            self.outline_editor.load_outline(project_id)
        elif module_name == "script":
            # 进入剧本编辑器
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.project_media_library.hide()
            self.outline_editor.hide()
            self.script_editor.show()
            self.script_editor.load_script(project_id)
        elif module_name == "media":
            # 进入项目素材库
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.outline_editor.hide()
            self.script_editor.hide()
            self.project_media_library.show()
            self.project_media_library.load_files(project_id=project_id)
        elif module_name == "storyboard":
            # 进入分镜编辑器
            logger.info(f"打开项目 {project_id} 的分镜模块")
            self.project_detail_page.hide()
            self.shot_editor.show()
            self.shot_editor.load_project(project_id)
        elif module_name == "character":
            # TODO: 进入角色管理
            logger.info(f"打开项目 {project_id} 的角色模块")

    def _on_project_detail_back(self) -> None:
        """从项目详情页返回项目网格。"""
        self.project_detail_page.hide()
        self.project_grid_page.show()
        self.project_grid_page.load_projects()

    def _on_project_media_back(self) -> None:
        """从项目素材库返回项目详情页。"""
        self.project_media_library.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_outline_editor_back(self) -> None:
        """从大纲编辑器返回项目详情页。"""
        self.outline_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_script_editor_back(self) -> None:
        """从剧本编辑器返回项目详情页。"""
        self.script_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_shot_editor_back(self) -> None:
        """从分镜编辑器返回项目详情页。"""
        self.shot_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_outline_next_step(self, outline_content: str) -> None:
        """大纲下一步：生成剧本并跳转到剧本编辑器。"""
        if not self._current_project_id:
            return

        # 显示生成中提示
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from qfluentwidgets import ProgressRing

        dialog = QDialog(self)
        dialog.setWindowTitle("生成剧本")
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)

        progress = ProgressRing()
        progress.setFixedSize(48, 48)
        layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel("正在使用 AI 生成剧本，请稍候...")
        label.setStyleSheet("font-size: 14px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        dialog.show()

        # 使用 QThread 异步生成剧本
        from PyQt6.QtCore import QThread, pyqtSignal

        class ScriptGenerateWorker(QThread):
            finished = pyqtSignal(str, list)  # (title, scenes)
            failed = pyqtSignal(str)

            def __init__(self, text_service, outline_content):
                super().__init__()
                self.text_service = text_service
                self.outline_content = outline_content

            def run(self):
                try:
                    title, scenes = self.text_service.generate_script(self.outline_content)
                    self.finished.emit(title, scenes)
                except Exception as e:
                    logger.exception("生成剧本失败")
                    self.failed.emit(str(e))

        def on_success(title: str, scenes: list):
            dialog.close()
            # 隐藏大纲编辑器，显示剧本编辑器
            self.outline_editor.hide()
            self.script_editor.show()
            self.script_editor.load_script(self._current_project_id, title, scenes)
            QMessageBox.information(self, "成功", f"剧本生成完成，共 {len(scenes)} 场！")

        def on_failed(error_msg: str):
            dialog.close()
            QMessageBox.critical(self, "生成失败", f"AI 生成剧本失败：{error_msg}")

        worker = ScriptGenerateWorker(self._text_model_service, outline_content)
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.start()

        # 保持 worker 引用避免被回收
        self._script_worker = worker

    def _on_generate_storyboard(self, project_id: str) -> None:
        """生成分镜（从剧本编辑器触发）。"""
        if not project_id:
            return

        # 获取剧本内容（合并所有场次）
        script = self._script_service.get_script_by_project(project_id)
        if not script:
            QMessageBox.warning(self, "错误", "未找到剧本")
            return

        scenes = self._script_service.list_scenes(script.id)
        if not scenes:
            QMessageBox.warning(self, "错误", "剧本中没有场次")
            return

        # 将所有场次合并为完整剧本文本
        script_content = f"{script.title}\n\n" if script.title else ""
        for scene in scenes:
            location_type_text = {
                "interior": "内景",
                "exterior": "外景",
                "interior_exterior": "内景/外景",
            }.get(scene.location_type.value, "内景")

            time_type_text = {
                "day": "日",
                "night": "夜",
                "dawn": "晨",
                "dusk": "黄昏",
                "evening": "傍晚",
                "custom": scene.time_detail,
            }.get(scene.time_type.value, "日")

            script_content += f"第{scene.scene_number}场  {location_type_text}  {scene.location}  -  {time_type_text}\n\n"
            script_content += f"{scene.content}\n\n"

        # 显示生成中提示
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from qfluentwidgets import ProgressRing

        dialog = QDialog(self)
        dialog.setWindowTitle("生成分镜")
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)

        progress = ProgressRing()
        progress.setFixedSize(48, 48)
        layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel("正在使用 AI 生成分镜头脚本，请稍候...")
        label.setStyleSheet("font-size: 14px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        dialog.show()

        # 使用 QThread 异步生成分镜
        from PyQt6.QtCore import QThread, pyqtSignal

        class StoryboardGenerateWorker(QThread):
            finished = pyqtSignal(list)  # shots
            failed = pyqtSignal(str)

            def __init__(self, text_service, script_content):
                super().__init__()
                self.text_service = text_service
                self.script_content = script_content

            def run(self):
                try:
                    shots = self.text_service.generate_storyboard(self.script_content)
                    self.finished.emit(shots)
                except Exception as e:
                    logger.exception("生成分镜失败")
                    self.failed.emit(str(e))

        def on_success(shots: list):
            dialog.close()
            self.script_editor.hide()
            self.shot_editor.show()
            self.shot_editor.load_project(project_id, shots)
            QMessageBox.information(self, "成功", f"分镜生成完成，共 {len(shots)} 个镜头！")

        def on_failed(error_msg: str):
            dialog.close()
            QMessageBox.critical(self, "生成失败", f"AI 生成分镜失败：{error_msg}")

        worker = StoryboardGenerateWorker(self._text_model_service, script_content)
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.start()

        # 保持 worker 引用避免被回收
        self._storyboard_worker = worker

    def _on_shot_video_generation(self, shot_id: str, scene_number: int, shot_number: int, prompt: str, project_id: str) -> None:
        """处理分镜视频生成请求。"""
        logger.info(f"分镜视频生成请求：shot_id={shot_id}, scene={scene_number}, shot={shot_number}, project={project_id}")

        # 获取项目属性（分辨率和比例）
        project = self._project_service.get_project(project_id)
        if not project:
            QMessageBox.warning(self, "错误", "项目不存在")
            return

        # 获取默认视频生成配置
        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(self, "配置错误", f"未配置 {provider_name} 的 API Key")
            return

        model_name = provider_cfg.default_model if provider_cfg else "wan2.7-t2v"

        # 创建隐藏对话（不在对话列表中显示）
        conversation_title = f"分镜视频-场{scene_number}镜{shot_number}"
        conv = self._service.create_conversation(provider_name, model_name, conversation_title, project_id=project_id, is_hidden=True)

        # 提交视频生成任务，使用项目的分辨率和比例参数
        try:
            # 合并项目参数和默认参数
            params = (provider_cfg.default_params if provider_cfg else {}).copy()
            params["resolution"] = project.resolution
            params["ratio"] = project.aspect_ratio

            msg = self._service.submit_task(
                conversation_id=conv.id,
                prompt=prompt,
                provider_name=provider_name,
                params=params
            )

            task_id = msg.task_id

            QMessageBox.information(
                self,
                "任务已提交",
                f"分镜视频生成任务已提交\n场次：{scene_number}，镜头：{shot_number}\n分辨率：{project.resolution} ({project.aspect_ratio})\n任务ID：{task_id}\n\n视频生成完成后将自动下载到项目素材库"
            )

            logger.info(f"分镜视频任务已提交：task_id={task_id}, shot_id={shot_id}, resolution={project.resolution}, aspect_ratio={project.aspect_ratio}")

        except Exception as e:
            logger.exception("提交视频生成任务失败")
            QMessageBox.critical(self, "错误", f"提交任务失败：{e}")

    def _on_batch_video_generation(self, shot_list: list) -> None:
        """批量串行生成分镜视频。"""
        if not shot_list:
            return

        project_id = shot_list[0]["project_id"]
        project = self._project_service.get_project(project_id)
        if not project:
            QMessageBox.warning(self, "错误", "项目不存在")
            self.shot_editor._generate_all_btn.setEnabled(True)
            return

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(self, "配置错误", f"未配置 {provider_name} 的 API Key")
            self.shot_editor._generate_all_btn.setEnabled(True)
            return

        model_name = provider_cfg.default_model if provider_cfg else "wan2.7-t2v"

        # 创建进度对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量生成视频")
        dialog.setModal(True)
        dialog.setFixedSize(420, 240)
        dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        from qfluentwidgets import ProgressBar, PushButton
        progress_bar = ProgressBar()
        progress_bar.setRange(0, len(shot_list))
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)

        status_label = QLabel(f"准备生成 {len(shot_list)} 个分镜视频...")
        status_label.setStyleSheet("font-size: 13px; color: #666;")
        status_label.setWordWrap(True)
        layout.addWidget(status_label)

        detail_label = QLabel("")
        detail_label.setStyleSheet("font-size: 12px; color: #999;")
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)

        stop_btn = PushButton("停止批量生成", dialog)
        stop_btn.setFixedHeight(32)
        stop_btn.clicked.connect(lambda: stop_btn.setEnabled(False))
        layout.addWidget(stop_btn)

        layout.addStretch()

        dialog.show()

        # 批量生成控制器
        batch = _BatchGenerationController(
            shot_list=shot_list,
            service=self._service,
            polling_service=self._polling_service,
            provider_name=provider_name,
            model_name=model_name,
            project=project,
            provider_cfg=provider_cfg,
        )

        def on_progress(index: int, total: int, scene: int, shot: int, status: str) -> None:
            progress_bar.setValue(index)
            status_label.setText(f"正在生成第 {index + 1}/{total} 个视频：场{scene}镜{shot}")
            detail_label.setText(status)

        def on_finished(success: int, failed: int, stopped: bool) -> None:
            dialog.close()
            self.shot_editor._generate_all_btn.setEnabled(True)
            title = "批量生成已停止" if stopped else "批量生成完成"
            QMessageBox.information(
                self, title,
                f"共 {len(shot_list)} 个任务\n成功：{success}\n失败：{failed}"
            )

        stop_btn.clicked.connect(batch.stop)
        batch.progress.connect(on_progress)
        batch.all_done.connect(lambda s, f: on_finished(s, f, False))
        batch.terminated.connect(lambda s, f: on_finished(s, f, True))
        batch.start()

        # 保持引用避免被回收
        self._batch_controller = batch

    # ───────── 侧边栏事件 ─────────

    def _on_new_conversation(self) -> None:
        self.media_library.hide()
        self.chat_area.show()
        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        model_name = provider_cfg.default_model if provider_cfg else "wan2.7-t2v"

        conv = self._service.create_conversation(provider_name, model_name, "新对话", project_id="")
        time_text = conv.created_at.strftime("%Y-%m-%d %H:%M")
        self.sidebar.add_conversation(conv.id, conv.title, time_text)
        self.sidebar.select_conversation(conv.id)
        self._current_conversation_id = conv.id
        self.chat_area.set_header(conv.title, model_name)
        self.chat_area.clear_messages()

    def _on_conversation_selected(self, conv_id: str) -> None:
        self.media_library.hide()
        self.chat_area.show()
        self._current_conversation_id = conv_id
        convs = [c for c in self._db.list_conversations() if c.id == conv_id]
        if convs:
            self.chat_area.set_header(convs[0].title, convs[0].model_name)
        self._load_messages(conv_id)

    def _on_conversation_deleted(self, conv_id: str) -> None:
        self._db.delete_conversation(conv_id)
        if self._current_conversation_id == conv_id:
            self._current_conversation_id = None
            self.chat_area.set_header("AI 视频生成", "未选择模型")
            self.chat_area.clear_messages()

    def _on_library(self) -> None:
        self.sidebar.clear_selection()
        self.chat_area.hide()
        self.media_library.show()
        self.media_library.load_files(project_id=None)

    def _on_jump_to_conversation(self, conversation_id: str, message_id: str) -> None:
        """从素材库跳转到对话，并定位到指定消息。"""
        # 切换到聊天区域
        self.media_library.hide()
        self.chat_area.show()

        # 选中对话
        self.sidebar.select_conversation(conversation_id)
        self._current_conversation_id = conversation_id

        # 加载对话和标题
        convs = [c for c in self._db.list_conversations() if c.id == conversation_id]
        if convs:
            self.chat_area.set_header(convs[0].title, convs[0].model_name)

        # 加载消息
        self._load_messages(conversation_id)

        # 定位到目标消息
        self._scroll_to_message(message_id)

    def _on_title_ready(self, conv_id: str, title: str) -> None:
        self._db.update_conversation_title(conv_id, title)

        # 更新直接生成模式的侧边栏
        self.sidebar.update_conversation_title(conv_id, title)

        # 更新项目管理模式的对话列表
        self.project_page.update_conversation_title(conv_id, title)

        # 更新当前聊天区域标题
        if conv_id == self._current_conversation_id:
            convs = [c for c in self._db.list_conversations() if c.id == conv_id]
            model_name = convs[0].model_name if convs else ""
            if self._current_mode == 0:
                self.chat_area.set_header(title, model_name)
            else:
                self.project_chat_area.set_header(title, model_name)

    # ───────── 消息发送 ─────────

    def _on_message_sent(self, text: str, params: dict) -> None:
        if not self._current_conversation_id:
            self._on_new_conversation()

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(
                self,
                "未配置 API Key",
                f"请先在设置中配置 {provider_name} 的 API Key。",
            )
            return

        conv_id = self._current_conversation_id
        is_first_message = len(self._db.list_messages(conv_id)) == 0

        now_str = _format_time(datetime.now())
        self.chat_area.add_user_message(text, now_str)
        self._service.add_user_message(conv_id, text)

        if is_first_message:
            self._chat_service.generate_title(conv_id, text)

        try:
            assistant_msg = self._service.submit_task(
                self._current_conversation_id, text, provider_name, params
            )
        except Exception as e:
            logger.exception("提交任务失败")
            card = self.chat_area.add_video_card()
            card.set_failed(str(e))
            return

        card = self.chat_area.add_ai_message_with_card("马上开始生成视频", now_str)
        card.open_folder_clicked.connect(self._open_folder)
        card.set_generating()
        self._video_cards[assistant_msg.id] = card

    # ───────── VideoService 信号 ─────────

    def _on_status_changed(self, message_id: str, status: str) -> None:
        card = self._video_cards.get(message_id)
        if not card:
            return
        if status == "downloading":
            card.set_downloading(0)
        elif status in ("generating", "running", "pending"):
            card.set_generating()

    def _on_download_progress(self, message_id: str, downloaded: int, total: int) -> None:
        card = self._video_cards.get(message_id)
        if not card or total <= 0:
            return
        pct = int(downloaded * 100 / total)
        card.set_downloading(pct)

    def _on_task_finished(self, message_id: str, local_path: str) -> None:
        card = self._video_cards.get(message_id)
        if card:
            meta = self._db.get_video_metadata_by_message(message_id) or {}
            card.set_completed(
                local_path,
                duration=meta.get("duration", 0),
                width=meta.get("width", 0),
                height=meta.get("height", 0),
            )
            card.play_btn.clicked.connect(lambda _, p=local_path: self._play_video(p))

    def _on_task_failed(self, message_id: str, error: str) -> None:
        card = self._video_cards.get(message_id)
        if card:
            card.set_failed(error)

    # ───────── 视频操作 ─────────

    def _play_video(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        try:
            os.startfile(path)
        except Exception as e:
            logger.warning("播放视频失败：%s", e)

    def _open_folder(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        folder = os.path.dirname(path)
        try:
            subprocess.Popen(f'explorer /select,"{path}"')
        except Exception as e:
            logger.warning("打开文件夹失败：%s", e)
            try:
                os.startfile(folder)
            except Exception:
                pass

    # ───────── 设置 / 生命周期 ─────────

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            self._service._providers.clear()
            self._chat_service.reset_provider()
            self._apply_default_provider()

    def _apply_default_provider(self) -> None:
        name = self._config.settings.default_provider or "dashscope"
        cfg = self._config.get_provider(name)
        model = cfg.default_model if cfg else "wan2.7-t2v"
        if self._current_conversation_id:
            self.chat_area.set_header(
                self.chat_area.title_label.text(), model
            )
        # 同步下载目录
        if self._config.settings.default_download_dir:
            download_dir = self._config.settings.default_download_dir
            self._media_service._download_dir = download_dir
            self._polling_service._download_dir = download_dir

    def _scroll_to_message(self, message_id: str) -> None:
        """滚动到指定消息位置。"""
        card = self._video_cards.get(message_id)
        if not card:
            return

        # 延迟滚动，确保布局完成
        QTimer.singleShot(100, lambda: self._do_scroll_to_card(card))

    def _do_scroll_to_card(self, card: VideoStatusCard) -> None:
        """执行滚动到卡片的操作。"""
        scroll_area = self.chat_area.scroll_area
        viewport_height = scroll_area.viewport().height()

        # 获取卡片在滚动区域中的位置
        card_pos = card.mapTo(scroll_area.widget(), card.pos())
        target_y = card_pos.y() - (viewport_height // 2) + (card.height() // 2)

        # 滚动到目标位置
        scroll_area.verticalScrollBar().setValue(max(0, target_y))

    # ───────── 项目管理模式事件 ─────────

    def _on_project_new_conversation(self, project_id: str) -> None:
        """项目模式：新建对话。"""
        self._current_project_id = project_id
        project = self._project_service.get_project(project_id)
        if not project:
            return

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        model_name = provider_cfg.default_model if provider_cfg else "wan2.7-t2v"

        conv = self._service.create_conversation(provider_name, model_name, "新对话", project_id=project_id)
        self._current_conversation_id = conv.id

        # 添加到项目页面的对话列表
        self.project_page.add_conversation_to_current_project(conv.id, conv.title)
        self.project_page.select_conversation(conv.id)

        # 更新聊天区域
        self.project_chat_area.set_header(conv.title, model_name)
        self.project_chat_area.clear_messages()

    def _on_project_conversation_selected(self, project_id: str, conv_id: str) -> None:
        """项目模式：选中对话。"""
        self._current_project_id = project_id
        self._current_conversation_id = conv_id
        convs = [c for c in self._db.list_conversations() if c.id == conv_id]
        if convs:
            self.project_chat_area.set_header(convs[0].title, convs[0].model_name)
        self._load_messages_for_project(conv_id)

    def _load_messages_for_project(self, conversation_id: str) -> None:
        """为项目模式加载消息。"""
        self.project_chat_area.clear_messages()
        for msg in self._db.list_messages(conversation_id):
            time_str = _format_time(msg.created_at)
            if msg.role == "user":
                self.project_chat_area.add_user_message(msg.content, time_str)
            else:
                card = self.project_chat_area.add_video_card(
                    message_text=msg.content, timestamp=time_str
                )
                self._video_cards[msg.id] = card
                card.open_folder_clicked.connect(self._open_folder)
                if msg.status.value == "completed" and msg.local_path:
                    meta = self._db.get_video_metadata_by_message(msg.id) or {}
                    card.set_completed(
                        msg.local_path,
                        duration=meta.get("duration", 0),
                        width=meta.get("width", 0),
                        height=meta.get("height", 0),
                    )
                    card.play_btn.clicked.connect(lambda _, p=msg.local_path: self._play_video(p))
                elif msg.status.value == "failed":
                    card.set_failed("生成失败")
                else:
                    card.set_generating()
        QTimer.singleShot(0, self.project_chat_area._scroll_to_bottom)

    def _on_project_conversation_deleted(self, conv_id: str) -> None:
        """项目模式：删除对话。"""
        self._db.delete_conversation(conv_id)
        if self._current_conversation_id == conv_id:
            self._current_conversation_id = None
            self.project_chat_area.set_header("选择对话", "")
            self.project_chat_area.clear_messages()

    def _on_project_message_sent(self, text: str, params: dict) -> None:
        """项目模式：发送消息。"""
        if not self._current_conversation_id or not self._current_project_id:
            return

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(
                self,
                "未配置 API Key",
                f"请先在设置中配置 {provider_name} 的 API Key。",
            )
            return

        conv_id = self._current_conversation_id
        is_first_message = len(self._db.list_messages(conv_id)) == 0

        now_str = _format_time(datetime.now())
        self.project_chat_area.add_user_message(text, now_str)
        self._service.add_user_message(conv_id, text)

        if is_first_message:
            self._chat_service.generate_title(conv_id, text)

        # 获取项目设置并添加到参数
        project = self._project_service.get_project(self._current_project_id)
        if project:
            # 将项目分辨率添加到参数（覆盖默认值）
            params["resolution"] = project.resolution
            params["ratio"] = project.aspect_ratio

        try:
            assistant_msg = self._service.submit_task(
                self._current_conversation_id, text, provider_name, params
            )
        except Exception as e:
            logger.exception("提交任务失败")
            card = self.project_chat_area.add_video_card()
            card.set_failed(str(e))
            return

        card = self.project_chat_area.add_ai_message_with_card("马上开始生成视频", now_str)
        card.open_folder_clicked.connect(self._open_folder)
        card.set_generating()
        self._video_cards[assistant_msg.id] = card

    # ───────── 设置 / 生命周期 ─────────
        self._polling_service.shutdown()
        self._db.close()
        super().closeEvent(event)
