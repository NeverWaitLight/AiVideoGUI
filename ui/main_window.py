"""主窗口：组装 UI 与 VideoService，编排完整生成链路。"""

from __future__ import annotations

import json
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
from service.character_service import CharacterService
from service.chat_service import ChatService
from service.image_service import ImageService
from service.media_service import MediaService
from service.story_outline_service import StoryOutlineService
from service.project_service import ProjectService
from service.screenplay_service import ScreenplayService
from service.storyboard_service import StoryboardService
from service.task_polling_service import TaskPollingService
from service.text_model_service import TextModelService
from service.video_service import VideoService, _PROVIDER_REGISTRY
from storage.database import DatabaseManager
from utils import paths
from ui.character_page import CharacterPage
from ui.chat_area import ChatArea
from ui.media_library import MediaLibrary
from ui.story_outline_editor import StoryOutlineEditor
from ui.project_detail_page import ProjectDetailPage
from ui.project_grid_page import ProjectGridPage
from ui.project_page import ProjectPage
from ui.screenplay_editor import ScreenplayEditor
from ui.settings_dialog import SettingsDialog
from ui.storyboard_editor import StoryboardEditor
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


def _workspace_root() -> str:
    return paths.workspace_root()


class _BatchGenerationController(QObject):
    """批量并行生成控制器：一次性提交所有任务到供应商，不等待前一个完成。"""

    progress = pyqtSignal(int, int, str)  # submitted_count, total, status
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
        self._success = 0
        self._failed = 0
        self._submitted_task_ids: set[str] = set()  # 追踪已提交的任务 ID
        self._stopped = False

    def start(self) -> None:
        """一次性提交所有任务到供应商。"""
        self._stopped = False
        self._polling.task_finished.connect(self._on_task_finished)
        self._polling.task_failed.connect(self._on_task_failed)

        # 并行提交所有任务
        submitted = 0
        for i, shot in enumerate(self._shot_list):
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]
            prompt = shot["prompt"]
            project_id = shot["project_id"]
            shot_id = shot.get("shot_id", "")
            reference_image = shot.get("reference_image", "")  # 获取参考图

            self.progress.emit(submitted, len(self._shot_list), f"正在提交场{scene_number}镜{shot_number}...")

            try:
                conv_title = f"分镜视频-场{scene_number}镜{shot_number}"
                conv = self._service.create_conversation(
                    self._provider_name, self._model_name, conv_title,
                    project_id=project_id, is_hidden=True,
                )

                params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
                params["resolution"] = self._project.resolution
                params["ratio"] = self._project.aspect_ratio

                # 预计算保存路径（相对于 workspace）：projects/{project_id}/场次号-镜头号-生成次数.mp4
                seq = self._service._db.get_next_storyboard_seq(scene_number, shot_number)
                save_path = os.path.join(
                    paths.projects_dir(paths.workspace_root()), str(project_id), f"{scene_number}-{shot_number}-{seq}.mp4"
                )

                msg = self._service.submit_task(
                    conversation_id=conv.id,
                    prompt=prompt,
                    provider_name=self._provider_name,
                    params=params,
                    save_path=save_path,
                    storyboard_id=shot_id,
                    reference_image=reference_image,  # 传递参考图
                )
                self._submitted_task_ids.add(msg.task_id)
                submitted += 1
                mode_info = "(r2v)" if reference_image else "(t2v)"
                logger.info("批量生成 [%d/%d] 场%d镜%d 已提交 %s task_id=%s save_path=%s",
                            submitted, len(self._shot_list), scene_number, shot_number, mode_info, msg.task_id, save_path)

            except Exception as e:
                logger.exception(f"批量生成提交失败：场{scene_number}镜{shot_number}")
                self._failed += 1
                self.progress.emit(submitted, len(self._shot_list), f"场{scene_number}镜{shot_number} 提交失败：{e}")

        if submitted > 0:
            self.progress.emit(submitted, len(self._shot_list), f"已提交 {submitted} 个任务，等待生成完成...")
            logger.info(f"批量生成：共提交 {submitted}/{len(self._shot_list)} 个任务")
        else:
            self._cleanup_and_finish()

    def stop(self) -> None:
        """停止监听任务完成（已提交的任务仍会在后台轮询完成）。"""
        if self._stopped:
            return
        self._stopped = True
        self.progress.emit(0, len(self._shot_list), "正在停止...")
        logger.info("批量生成已收到停止请求")
        self._cleanup_and_terminate()

    def _cleanup_and_terminate(self) -> None:
        """断开轮询信号并通知 UI 终止。"""
        try:
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.terminated.emit(self._success, self._failed)

    def _cleanup_and_finish(self) -> None:
        """断开轮询信号并通知 UI 全部完成。"""
        try:
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.all_done.emit(self._success, self._failed)

    def _on_task_finished(self, message_id: str, local_path: str, storyboard_id: int = 0) -> None:
        """任务完成回调，检查是否属于本批次。"""
        msg = self._service._db.get_message(message_id)
        if not msg or msg.task_id not in self._submitted_task_ids:
            return

        self._success += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)

        self.progress.emit(
            completed, total_submitted,
            f"已完成 {self._success}/{total_submitted}，失败 {self._failed}"
        )
        logger.info(f"批量生成进度：{self._success} 成功，{self._failed} 失败，共 {total_submitted} 个任务")

        # 检查是否全部完成
        if completed >= total_submitted:
            self._cleanup_and_finish()

    def _on_task_failed(self, message_id: str, error: str) -> None:
        """任务失败回调，检查是否属于本批次。"""
        msg = self._service._db.get_message(message_id)
        if not msg or msg.task_id not in self._submitted_task_ids:
            return

        self._failed += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)

        self.progress.emit(
            completed, total_submitted,
            f"已完成 {self._success}/{total_submitted}，失败 {self._failed}"
        )
        logger.warning(f"批量生成进度：{self._success} 成功，{self._failed} 失败，共 {total_submitted} 个任务")

        # 检查是否全部完成
        if completed >= total_submitted:
            self._cleanup_and_finish()


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
        self._current_project_id: int | None = None

        # ── 初始化基础设施 ──
        root = _workspace_root()
        data_dir = paths.data_dir(root)
        cache_dir = paths.cache_dir(root)
        ws_dir = paths.workspace_dir(root)
        chat_dir = paths.chat_dir(root)
        for d in (data_dir, cache_dir, ws_dir, chat_dir):
            os.makedirs(d, exist_ok=True)

        self._root = root
        self._db = DatabaseManager(os.path.join(data_dir, "ai-video-gui.db"))
        self._config = ConfigManager(os.path.join(data_dir, "config.json"))

        # VideoService 仅负责对话和任务提交
        self._service = VideoService(self._db, self._config)
        self._chat_service = ChatService(self._config)

        # 项目服务
        self._project_service = ProjectService(self._db, self._root)

        # 故事大纲服务
        self._story_outline_service = StoryOutlineService(self._db)

        # 剧本服务
        self._screenplay_service = ScreenplayService(self._db)

        # 分镜服务
        self._storyboard_service = StoryboardService(self._db)

        # 角色服务
        self._character_service = CharacterService(self._db)

        # 文本模型服务
        self._text_model_service = TextModelService(self._config)

        # 图片生成服务
        self._image_service = ImageService(self._config)

        # 素材库服务
        self._media_service = MediaService(self._db, self._root)

        # 全局任务轮询服务
        self._polling_service = TaskPollingService(
            db=self._db,
            config=self._config,
            workspace_root=self._root,
            provider_registry=_PROVIDER_REGISTRY,
        )
        self._polling_service.set_media_service(self._media_service)

        self._setup_ui()
        self._connect_signals()
        self._load_conversations()

        # 启动全局轮询服务
        self._polling_service.start()

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
        self.project_detail_page = ProjectDetailPage(self._project_service, self._db)
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

        # 第三层：故事大纲编辑器
        self.story_outline_editor = StoryOutlineEditor(self._story_outline_service, self._text_model_service)
        layout.addWidget(self.story_outline_editor)
        self.story_outline_editor.hide()

        # 第三层：剧本编辑器
        self.screenplay_editor = ScreenplayEditor(self._screenplay_service)
        layout.addWidget(self.screenplay_editor)
        self.screenplay_editor.hide()

        # 第三层：分镜编辑器
        self.storyboard_editor = StoryboardEditor(
            self._storyboard_service, self._screenplay_service, media_service=self._media_service
        )
        layout.addWidget(self.storyboard_editor)
        self.storyboard_editor.hide()

        # 第三层：角色管理页
        self.character_page = CharacterPage(self._character_service)
        layout.addWidget(self.character_page)
        self.character_page.hide()

        # 第三层：视频播放器
        from ui.video_player_page import VideoPlayerPage
        self.video_player_page = VideoPlayerPage(self._db)
        layout.addWidget(self.video_player_page)
        self.video_player_page.hide()

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

        # 故事大纲编辑器信号
        self.story_outline_editor.back_clicked.connect(self._on_story_outline_editor_back)
        self.story_outline_editor.next_step_clicked.connect(self._on_story_outline_next_step)

        # 剧本编辑器信号
        self.screenplay_editor.back_clicked.connect(self._on_screenplay_editor_back)
        self.screenplay_editor.generate_storyboard_clicked.connect(self._on_generate_storyboard)

        # 分镜编辑器信号
        self.storyboard_editor.back_clicked.connect(self._on_shot_editor_back)
        self.storyboard_editor.preview_prompt_requested.connect(self._on_preview_prompt_request)
        self.storyboard_editor.video_generation_requested.connect(self._on_shot_video_generation)
        self.storyboard_editor.batch_video_generation_requested.connect(self._on_batch_video_generation)
        self.storyboard_editor.design_image_generation_requested.connect(self._on_generate_design_image)
        self.storyboard_editor.batch_design_image_generation_requested.connect(self._on_batch_generate_design_images)

        # 角色管理页信号
        self.character_page.back_clicked.connect(self._on_character_page_back)
        self.character_page.design_image_generation_requested.connect(self._on_generate_character_design_image)

        # 视频播放器信号
        self.video_player_page.back_clicked.connect(self._on_video_player_back)

        # 直接生成模式信号
        self.sidebar.new_conversation_clicked.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.conversation_deleted.connect(self._on_conversation_deleted)
        self.tab_bar.library_clicked.connect(self._on_library)
        self.tab_bar.settings_clicked.connect(self._on_settings)
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
            self.story_outline_editor.hide()
            self.project_conversation_widget.hide()
            self.project_grid_page.load_projects()

    def _on_project_grid_selected(self, project_id: int) -> None:
        """从网格页面点击项目，进入详情页面。"""
        self._current_project_id = project_id
        # 隐藏网格页面，显示详情页面
        self.project_grid_page.hide()
        self.project_detail_page.show()
        self.project_detail_page.set_project(project_id)

    def _on_project_module_selected(self, project_id: int, module_name: str) -> None:
        """项目模块被选中。"""
        self._current_project_id = project_id

        if module_name == "play":
            # 进入视频播放器
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.project_media_library.hide()
            self.story_outline_editor.hide()
            self.screenplay_editor.hide()
            self.storyboard_editor.hide()
            self.character_page.hide()
            self.video_player_page.show()
            self.video_player_page.load_playlist(project_id)
        elif module_name == "outline":
            # 进入故事大纲编辑器
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.project_media_library.hide()
            self.screenplay_editor.hide()
            self.storyboard_editor.hide()
            self.character_page.hide()
            self.video_player_page.hide()
            self.story_outline_editor.show()
            self.story_outline_editor.load_story_outline(project_id)
        elif module_name == "script":
            # 进入剧本编辑器
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.project_media_library.hide()
            self.story_outline_editor.hide()
            self.storyboard_editor.hide()
            self.character_page.hide()
            self.video_player_page.hide()
            self.screenplay_editor.show()
            self.screenplay_editor.load_script(project_id)
        elif module_name == "media":
            # 进入项目素材库
            self.project_detail_page.hide()
            self.project_conversation_widget.hide()
            self.story_outline_editor.hide()
            self.screenplay_editor.hide()
            self.storyboard_editor.hide()
            self.character_page.hide()
            self.video_player_page.hide()
            self.project_media_library.show()
            self.project_media_library.load_files(project_id=project_id)
        elif module_name == "storyboard":
            # 进入分镜编辑器
            logger.info(f"打开项目 {project_id} 的分镜模块")
            self.project_detail_page.hide()
            self.character_page.hide()
            self.video_player_page.hide()
            self.storyboard_editor.show()
            self.storyboard_editor.load_project(project_id)
        elif module_name == "character":
            # 进入角色管理
            logger.info(f"打开项目 {project_id} 的角色模块")
            self.project_detail_page.hide()
            self.story_outline_editor.hide()
            self.screenplay_editor.hide()
            self.storyboard_editor.hide()
            self.video_player_page.hide()
            self.project_media_library.hide()
            self.character_page.show()
            self.character_page.load_project(project_id)

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

    def _on_story_outline_editor_back(self) -> None:
        """从故事大纲编辑器返回项目详情页。"""
        self.story_outline_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_screenplay_editor_back(self) -> None:
        """从剧本编辑器返回项目详情页。"""
        self.screenplay_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_shot_editor_back(self) -> None:
        """从分镜编辑器返回项目详情页。"""
        self.storyboard_editor.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_character_page_back(self) -> None:
        """从角色管理页返回项目详情页。"""
        self.character_page.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_video_player_back(self) -> None:
        """从视频播放器返回项目详情页。"""
        self.video_player_page.hide()
        self.project_detail_page.show()
        if self._current_project_id:
            self.project_detail_page.set_project(self._current_project_id)

    def _on_story_outline_next_step(self, outline_content: str) -> None:
        """大纲下一步：生成剧本并跳转到剧本编辑器。"""
        if not self._current_project_id:
            return

        # 显示生成中提示
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from qfluentwidgets import ProgressRing

        self._script_dialog = QDialog(self)
        self._script_dialog.setWindowTitle("生成剧本")
        self._script_dialog.setModal(True)
        self._script_dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(self._script_dialog)
        layout.setSpacing(20)

        progress = ProgressRing()
        progress.setFixedSize(48, 48)
        layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel("正在使用 AI 生成剧本，请稍候...")
        label.setStyleSheet("font-size: 14px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self._script_dialog.show()

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
            try:
                self._script_dialog.close()
                self.story_outline_editor.hide()
                self.screenplay_editor.show()
                self.screenplay_editor.load_script(self._current_project_id, title, scenes)
                QMessageBox.information(self, "成功", f"剧本生成完成，共 {len(scenes)} 场！")
            except Exception as e:
                logger.exception("生成剧本后处理失败")
                self._script_dialog.close()
                QMessageBox.critical(self, "错误", f"剧本生成后处理失败：{e}")

        def on_failed(error_msg: str):
            try:
                self._script_dialog.close()
            except Exception:
                pass
            QMessageBox.critical(self, "生成失败", f"AI 生成剧本失败：{error_msg}")

        worker = ScriptGenerateWorker(self._text_model_service, outline_content)
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.start()

        # 保持 worker 引用避免被回收
        self._script_worker = worker

    def _on_generate_storyboard(self, project_id: int) -> None:
        """生成分镜（从剧本编辑器触发）。"""
        if not project_id:
            return

        # 获取剧本内容（合并所有场次）
        scenes = self._screenplay_service.list_scenes(project_id)
        if not scenes:
            QMessageBox.warning(self, "错误", "剧本中没有场次")
            return

        # 将所有场次合并为完整剧本文本
        script_content = ""
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

        self._storyboard_dialog = QDialog(self)
        self._storyboard_dialog.setWindowTitle("生成分镜")
        self._storyboard_dialog.setModal(True)
        self._storyboard_dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(self._storyboard_dialog)
        layout.setSpacing(20)

        progress = ProgressRing()
        progress.setFixedSize(48, 48)
        layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel("正在使用 AI 生成分镜头脚本，请稍候...")
        label.setStyleSheet("font-size: 14px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self._storyboard_dialog.show()

        # 使用 QThread 异步生成分镜
        from PyQt6.QtCore import QThread, pyqtSignal

        class StoryboardGenerateWorker(QThread):
            finished = pyqtSignal(dict)  # {"shots": list, "characters": list}
            failed = pyqtSignal(str)

            def __init__(self, text_service, script_content):
                super().__init__()
                self.text_service = text_service
                self.script_content = script_content

            def run(self):
                try:
                    result = self.text_service.generate_storyboard(self.script_content)
                    self.finished.emit(result)
                except Exception as e:
                    logger.exception("生成分镜失败")
                    self.failed.emit(str(e))

        def on_success(result: dict):
            try:
                self._storyboard_dialog.close()
                shots = result.get("shots", [])
                characters = result.get("characters", [])

                # 自动保存提取的角色到数据库
                if characters and project_id:
                    self._save_extracted_characters(project_id, characters)

                self.screenplay_editor.hide()
                self.storyboard_editor.show()
                self.storyboard_editor.load_project(project_id, shots)
                char_info = f"，{len(characters)} 个角色" if characters else ""
                QMessageBox.information(self, "成功", f"分镜生成完成，共 {len(shots)} 个镜头{char_info}！")
            except Exception as e:
                logger.exception("生成分镜后处理失败")
                self._storyboard_dialog.close()
                QMessageBox.critical(self, "错误", f"分镜生成后处理失败：{e}")

        def on_failed(error_msg: str):
            try:
                self._storyboard_dialog.close()
            except Exception:
                pass
            QMessageBox.critical(self, "生成失败", f"AI 生成分镜失败：{error_msg}")

        worker = StoryboardGenerateWorker(self._text_model_service, script_content)
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.start()

        # 保持 worker 引用避免被回收
        self._storyboard_worker = worker

    def _save_extracted_characters(self, project_id: int, characters: list[dict]) -> None:
        """将 AI 提取的角色保存到数据库（跳过已存在的引用代号）。"""
        import uuid
        from datetime import datetime
        from models.data_models import Character

        new_chars = []
        for char_data in characters:
            ref_code = char_data.get("ref_code", "")
            if not ref_code:
                continue
            # 跳过已存在的角色（按 ref_code 去重）
            existing = self._character_service.get_by_ref_code(project_id, ref_code)
            if existing:
                logger.info(f"角色 {ref_code} 已存在，跳过")
                continue
            new_chars.append(Character(
                id=0,
                uuid=str(uuid.uuid4()),
                project_id=project_id,
                name=char_data.get("name", ""),
                ref_code=ref_code,
                description=char_data.get("description", ""),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ))

        if new_chars:
            self._character_service.batch_create_characters(new_chars)
            logger.info(f"自动保存 {len(new_chars)} 个角色到项目 {project_id}")

    def _on_preview_prompt_request(self, storyboard_id: int, project_id: int) -> None:
        """预览将发送给万象的请求参数。"""
        storyboard = self._storyboard_service.get_storyboard(storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            return

        prompt = storyboard.visual_content
        if not prompt.strip():
            QMessageBox.warning(self, "提示", "分镜画面内容为空")
            return

        # 用角色形象描述增强提示词（与视频生成流程一致）
        prompt = self._character_service.enrich_prompt_with_characters(prompt, project_id)

        project = self._project_service.get_project(project_id)
        if not project:
            QMessageBox.warning(self, "错误", "项目不存在")
            return

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg:
            QMessageBox.warning(self, "配置错误", f"未配置 {provider_name}")
            return

        try:
            provider = self._service.get_provider(provider_name)
        except KeyError as e:
            QMessageBox.warning(self, "配置错误", str(e))
            return

        params = (provider_cfg.default_params if provider_cfg else {}).copy()
        params["resolution"] = project.resolution
        params["ratio"] = project.aspect_ratio
        # 添加默认生成参数（如果 default_params 中未指定）
        params.setdefault("duration", 5)
        params.setdefault("prompt_extend", True)
        params.setdefault("watermark", False)

        payload = provider.build_payload(prompt, params)

        # 弹出展示对话框
        from qfluentwidgets import TextEdit as FluentTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"提示词预览 — 场{storyboard.scene_number}镜{storyboard.shot_number}"
        )
        dialog.setModal(True)
        dialog.resize(560, 480)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        prompt_label = QLabel("增强后的提示词：")
        layout.addWidget(prompt_label)

        prompt_edit = FluentTextEdit()
        prompt_edit.setReadOnly(True)
        prompt_edit.setPlainText(prompt)
        prompt_edit.setFixedHeight(140)
        layout.addWidget(prompt_edit)

        payload_label = QLabel("发送给万象的请求体（JSON）：")
        layout.addWidget(payload_label)

        payload_edit = FluentTextEdit()
        payload_edit.setReadOnly(True)
        payload_edit.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
        layout.addWidget(payload_edit, 1)

        dialog.exec()

    def _on_shot_video_generation(self, shot_id: int, scene_number: int, shot_number: int, prompt: str, project_id: int, design_image: str = "") -> None:
        """处理分镜视频生成请求。"""
        logger.info(f"分镜视频生成请求：shot_id={shot_id}, scene={scene_number}, shot={shot_number}, project={project_id}, design_image={design_image}")

        # 用角色形象描述增强提示词
        prompt = self._character_service.enrich_prompt_with_characters(prompt, project_id)

        # 确定参考图：优先使用分镜设计图，否则查找角色设计图
        reference_image = ""
        if design_image and os.path.exists(design_image):
            reference_image = design_image
            logger.info(f"使用分镜设计图作为参考：{design_image}")
        else:
            # 尝试从项目角色中找到第一个有设计图的角色
            characters = self._character_service.list_characters(project_id)
            for char in characters:
                if char.design_image and os.path.exists(char.design_image):
                    reference_image = char.design_image
                    logger.info(f"使用角色 {char.name} 的设计图作为参考：{char.design_image}")
                    break

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
            # 添加默认生成参数（如果 default_params 中未指定）
            params.setdefault("duration", 5)
            params.setdefault("prompt_extend", True)
            params.setdefault("watermark", False)

            # 预计算保存路径（相对于 workspace）：projects/{project_id}/场次号-镜头号-生成次数.mp4
            seq = self._db.get_next_storyboard_seq(scene_number, shot_number)
            save_path = os.path.join(
                paths.projects_dir(paths.workspace_root()), str(project_id), f"{scene_number}-{shot_number}-{seq}.mp4"
            )

            msg = self._service.submit_task(
                conversation_id=conv.id,
                prompt=prompt,
                provider_name=provider_name,
                params=params,
                save_path=save_path,
                storyboard_id=shot_id,
                reference_image=reference_image,  # 传递参考图路径
            )

            task_id = msg.task_id

            # 根据是否使用参考图显示不同提示
            mode_info = "参考生视频 (r2v)" if reference_image else "文生视频 (t2v)"
            ref_info = f"\n参考图：{reference_image}" if reference_image else ""

            QMessageBox.information(
                self,
                "任务已提交",
                f"分镜视频生成任务已提交 ({mode_info})\n场次：{scene_number}，镜头：{shot_number}\n保存路径：{save_path}\n分辨率：{project.resolution} ({project.aspect_ratio}){ref_info}\n任务ID：{task_id}\n\n视频生成完成后将自动下载到项目素材库"
            )

            logger.info("分镜视频任务已提交：task_id=%s, shot_id=%s, save_path=%s", task_id, shot_id, save_path)

        except Exception as e:
            logger.exception("提交视频生成任务失败")
            QMessageBox.critical(self, "错误", f"提交任务失败：{e}")

    def _on_batch_video_generation(self, shot_list: list) -> None:
        """批量并行生成分镜视频。"""
        if not shot_list:
            return

        project_id = shot_list[0]["project_id"]

        # 查询项目角色设计图（作为备选参考图）
        characters = self._character_service.list_characters(project_id)
        fallback_character_image = ""
        for char in characters:
            if char.design_image and os.path.exists(char.design_image):
                fallback_character_image = char.design_image
                logger.info(f"找到备选角色设计图：{char.name} - {char.design_image}")
                break

        # 用角色形象描述增强所有提示词，并确定每个分镜的参考图
        for shot_item in shot_list:
            shot_item["prompt"] = self._character_service.enrich_prompt_with_characters(
                shot_item["prompt"], project_id
            )
            # 确定参考图：优先使用分镜设计图，否则使用角色设计图
            design_image = shot_item.get("design_image", "")
            if design_image and os.path.exists(design_image):
                shot_item["reference_image"] = design_image
            elif fallback_character_image:
                shot_item["reference_image"] = fallback_character_image
            else:
                shot_item["reference_image"] = ""

        project = self._project_service.get_project(project_id)
        if not project:
            QMessageBox.warning(self, "错误", "项目不存在")
            self.storyboard_editor._generate_all_btn.setEnabled(True)
            return

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(self, "配置错误", f"未配置 {provider_name} 的 API Key")
            self.storyboard_editor._generate_all_btn.setEnabled(True)
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

        def on_progress(completed: int, total: int, status: str) -> None:
            progress_bar.setValue(completed)
            status_label.setText(f"已提交 {total} 个任务")
            detail_label.setText(status)

        def on_finished(success: int, failed: int, stopped: bool) -> None:
            dialog.close()
            self.storyboard_editor._generate_all_btn.setEnabled(True)
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

    def _on_generate_design_image(self, storyboard_id: int, project_id: int) -> None:
        """AI 生成分镜设计图：先用文本模型生成英文提示词，再调用图片生成 API。"""
        logger.info(f"AI 生成设计图：storyboard_id={storyboard_id}, project_id={project_id}")

        storyboard = self._storyboard_service.get_storyboard(storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            self.storyboard_editor.detail_editor.set_design_image_result("")
            return

        # 景别映射
        shot_size_map = {
            "extreme_close_up": "特写",
            "close_up": "近景",
            "medium_shot": "中景",
            "full_shot": "全景",
            "long_shot": "远景",
            "extreme_long_shot": "大远景",
        }
        shot_size_text = shot_size_map.get(storyboard.shot_size.value, "中景")

        # 获取角色信息增强提示词
        character_info = ""
        characters = self._character_service.list_characters(project_id)
        matched_chars = []
        for char in characters:
            if char.name in storyboard.visual_content or char.ref_code in storyboard.visual_content:
                matched_chars.append(char)
        if matched_chars:
            char_parts = []
            for c in matched_chars:
                traits = self._character_service.extract_fixed_traits(c.description)
                if traits:
                    char_parts.append(f"{c.name}（{c.ref_code}）：{traits}")
            character_info = "\n".join(char_parts)

        # 更新 UI 状态为生成中
        self.storyboard_editor.detail_editor.set_generating_design(True)

        # 显示进度对话框
        from qfluentwidgets import IndeterminateProgressBar

        dialog = QDialog(self)
        dialog.setWindowTitle("生成设计图")
        dialog.setModal(True)
        dialog.setFixedSize(320, 120)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        progress = IndeterminateProgressBar()
        progress.start()
        layout.addWidget(progress)

        status_label = QLabel("正在生成设计图提示词...")
        status_label.setStyleSheet("font-size: 13px; color: #666;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        dialog.show()

        # 使用 QThread 异步生成
        from PyQt6.QtCore import QThread

        class DesignImageWorker(QThread):
            finished = pyqtSignal(str)  # image_path
            failed = pyqtSignal(str)  # error_message
            progress_update = pyqtSignal(str)  # status text

            def __init__(self, text_service, image_service, storyboard_service,
                         storyboard, shot_size_text, character_info, project_id):
                super().__init__()
                self._text_service = text_service
                self._image_service = image_service
                self._storyboard_service = storyboard_service
                self._storyboard = storyboard
                self._shot_size_text = shot_size_text
                self._character_info = character_info
                self._project_id = project_id

            def run(self):
                try:
                    # Step 1: 用文本模型生成英文图片提示词
                    self.progress_update.emit("正在生成设计图提示词...")
                    image_prompt = self._text_service.generate_design_image_prompt(
                        visual_content=self._storyboard.visual_content,
                        shot_size=self._shot_size_text,
                        camera_movement=self._storyboard.camera_movement,
                        dialogue=self._storyboard.dialogue,
                        notes=self._storyboard.notes,
                        character_info=self._character_info,
                    )
                    logger.info(f"设计图提示词：{image_prompt}")

                    # Step 2: 调用图片生成 API
                    self.progress_update.emit("正在调用图片生成模型...")
                    save_path = os.path.join(
                        paths.projects_dir(paths.workspace_root()),
                        str(self._project_id),
                        f"design-{self._storyboard.scene_number}-{self._storyboard.shot_number}.png",
                    )
                    result_path = self._image_service.generate(
                        prompt=image_prompt,
                        save_path=save_path,
                    )

                    # Step 3: 保存路径到数据库
                    self._storyboard_service.update_storyboard(
                        storyboard_id=self._storyboard.id,
                        design_image=result_path,
                    )
                    logger.info(f"设计图生成完成：{result_path}")
                    self.finished.emit(result_path)

                except Exception as e:
                    logger.exception("生成设计图失败")
                    self.failed.emit(str(e))

        def on_success(image_path: str):
            try:
                dialog.close()
            except Exception:
                pass
            self.storyboard_editor.detail_editor.set_design_image_result(image_path)
            QMessageBox.information(self, "成功", "分镜设计图生成完成！")

        def on_failed(error_msg: str):
            try:
                dialog.close()
            except Exception:
                pass
            self.storyboard_editor.detail_editor.set_design_image_result("")
            QMessageBox.critical(self, "生成失败", f"AI 生成设计图失败：{error_msg}")

        def on_progress_update(text: str):
            status_label.setText(text)

        worker = DesignImageWorker(
            self._text_model_service,
            self._image_service,
            self._storyboard_service,
            storyboard,
            shot_size_text,
            character_info,
            project_id,
        )
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.progress_update.connect(on_progress_update)
        worker.start()

        # 保持引用避免被回收
        self._design_image_worker = worker

    def _on_batch_generate_design_images(self, shot_list: list[dict]) -> None:
        """批量生成分镜设计图（逐个处理，显示进度）。"""
        logger.info(f"批量生成设计图：共 {len(shot_list)} 个分镜")

        if not shot_list:
            return

        # 显示进度对话框
        from qfluentwidgets import ProgressBar

        dialog = QDialog(self)
        dialog.setWindowTitle("批量生成设计图")
        dialog.setModal(True)
        dialog.setFixedSize(400, 150)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        status_label = QLabel("准备生成...")
        status_label.setStyleSheet("font-size: 13px; color: #666;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        progress_bar = ProgressBar()
        progress_bar.setRange(0, len(shot_list))
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)

        detail_label = QLabel("")
        detail_label.setStyleSheet("font-size: 12px; color: #999;")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail_label)

        dialog.show()

        # 使用 QThread 异步生成
        from PyQt6.QtCore import QThread

        class BatchDesignImageWorker(QThread):
            progress_update = pyqtSignal(int, str, str)  # (index, status, detail)
            finished = pyqtSignal(int, int)  # (success_count, total_count)
            failed = pyqtSignal(str)

            def __init__(self, text_service, image_service, storyboard_service, character_service, shot_list):
                super().__init__()
                self._text_service = text_service
                self._image_service = image_service
                self._storyboard_service = storyboard_service
                self._character_service = character_service
                self._shot_list = shot_list

            def run(self):
                success_count = 0
                total = len(self._shot_list)

                # 景别映射
                shot_size_map = {
                    "extreme_close_up": "特写",
                    "close_up": "近景",
                    "medium_shot": "中景",
                    "full_shot": "全景",
                    "long_shot": "远景",
                    "extreme_long_shot": "大远景",
                }

                for idx, shot_data in enumerate(self._shot_list, start=1):
                    try:
                        storyboard_id = shot_data["storyboard_id"]
                        project_id = shot_data["project_id"]
                        scene_number = shot_data["scene_number"]
                        shot_number = shot_data["shot_number"]

                        self.progress_update.emit(
                            idx - 1,
                            f"正在生成 {scene_number}-{shot_number} 镜设计图...",
                            f"({idx}/{total})"
                        )

                        # 获取角色信息
                        visual_content = shot_data["visual_content"]
                        characters = self._character_service.list_characters(project_id)
                        matched_chars = []
                        for char in characters:
                            if char.name in visual_content or char.ref_code in visual_content:
                                matched_chars.append(char)

                        character_info = ""
                        if matched_chars:
                            char_parts = []
                            for c in matched_chars:
                                traits = self._character_service.extract_fixed_traits(c.description)
                                if traits:
                                    char_parts.append(f"{c.name}（{c.ref_code}）：{traits}")
                            character_info = "\n".join(char_parts)

                        # Step 1: 生成英文提示词
                        shot_size_text = shot_size_map.get(shot_data["shot_size"].value, "中景")
                        image_prompt = self._text_service.generate_design_image_prompt(
                            visual_content=visual_content,
                            shot_size=shot_size_text,
                            camera_movement=shot_data.get("camera_movement", ""),
                            dialogue=shot_data.get("dialogue", ""),
                            notes=shot_data.get("notes", ""),
                            character_info=character_info,
                        )
                        logger.info(f"设计图提示词 [{scene_number}-{shot_number}]：{image_prompt}")

                        # Step 2: 调用图片生成 API
                        import os
                        from utils import paths
                        save_path = os.path.join(
                            paths.projects_dir(paths.workspace_root()),
                            str(project_id),
                            f"design-{scene_number}-{shot_number}.png",
                        )
                        result_path = self._image_service.generate(
                            prompt=image_prompt,
                            save_path=save_path,
                        )

                        # Step 3: 保存路径到数据库
                        self._storyboard_service.update_storyboard(
                            storyboard_id=storyboard_id,
                            design_image=result_path,
                        )
                        logger.info(f"设计图生成完成 [{scene_number}-{shot_number}]：{result_path}")
                        success_count += 1

                    except Exception as e:
                        logger.exception(f"生成设计图失败 [{scene_number}-{shot_number}]")
                        # 继续处理下一个，不中断整个批量任务

                self.finished.emit(success_count, total)

        def on_progress(index: int, status: str, detail: str):
            status_label.setText(status)
            detail_label.setText(detail)
            progress_bar.setValue(index)

        def on_finished(success_count: int, total_count: int):
            try:
                dialog.close()
            except Exception:
                pass
            self.storyboard_editor._generate_all_designs_btn.setEnabled(True)
            self.storyboard_editor._load_storyboards()  # 刷新列表显示新的设计图
            QMessageBox.information(
                self,
                "批量生成完成",
                f"成功生成 {success_count}/{total_count} 个分镜设计图。"
            )

        def on_failed(error_msg: str):
            try:
                dialog.close()
            except Exception:
                pass
            self.storyboard_editor._generate_all_designs_btn.setEnabled(True)
            QMessageBox.critical(self, "批量生成失败", f"批量生成设计图失败：{error_msg}")

        worker = BatchDesignImageWorker(
            self._text_model_service,
            self._image_service,
            self._storyboard_service,
            self._character_service,
            shot_list,
        )
        worker.progress_update.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.start()

        # 保持引用避免被回收
        self._batch_design_image_worker = worker

    def _on_generate_character_design_image(self, character_uuid: str, project_id: int) -> None:
        """AI 生成角色设计图：先用文本模型生成英文提示词，再调用图片生成 API。"""
        logger.info(f"AI 生成角色设计图：character_uuid={character_uuid}, project_id={project_id}")

        character = self._character_service.get_character(character_uuid)
        if not character:
            QMessageBox.warning(self, "错误", "角色不存在")
            self.character_page.detail_page.set_design_image_result("")
            return

        if not character.description:
            QMessageBox.warning(self, "提示", "请先编辑角色形象描述")
            self.character_page.detail_page.set_design_image_result("")
            return

        # 更新 UI 状态为生成中
        self.character_page.detail_page.set_generating_design(True)

        # 显示进度对话框
        from qfluentwidgets import IndeterminateProgressBar

        dialog = QDialog(self)
        dialog.setWindowTitle("生成角色设计图")
        dialog.setModal(True)
        dialog.setFixedSize(320, 120)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        progress = IndeterminateProgressBar()
        progress.start()
        layout.addWidget(progress)

        status_label = QLabel("正在生成设计图提示词...")
        status_label.setStyleSheet("font-size: 13px; color: #666;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        dialog.show()

        # 使用 QThread 异步生成
        from PyQt6.QtCore import QThread

        class CharacterDesignImageWorker(QThread):
            finished = pyqtSignal(str)
            failed = pyqtSignal(str)
            progress_update = pyqtSignal(str)

            def __init__(self, text_service, image_service, character_service,
                         character, project_id):
                super().__init__()
                self._text_service = text_service
                self._image_service = image_service
                self._character_service = character_service
                self._character = character
                self._project_id = project_id

            def run(self):
                try:
                    # Step 1: 用文本模型生成英文图片提示词
                    self.progress_update.emit("正在生成设计图提示词...")
                    image_prompt = self._text_service.generate_character_design_image_prompt(
                        character_name=self._character.name,
                        description=self._character.description,
                    )
                    logger.info(f"角色设计图提示词：{image_prompt}")

                    # Step 2: 调用图片生成 API
                    self.progress_update.emit("正在调用图片生成模型...")
                    save_path = os.path.join(
                        paths.projects_dir(paths.workspace_root()),
                        str(self._project_id),
                        f"character-{self._character.uuid}.png",
                    )
                    result_path = self._image_service.generate(
                        prompt=image_prompt,
                        save_path=save_path,
                    )

                    # Step 3: 保存路径到数据库
                    self._character_service.update_character(
                        character_uuid=self._character.uuid,
                        design_image=result_path,
                    )
                    logger.info(f"角色设计图生成完成：{result_path}")
                    self.finished.emit(result_path)

                except Exception as e:
                    logger.exception("生成角色设计图失败")
                    self.failed.emit(str(e))

        def on_success(image_path: str):
            try:
                dialog.close()
            except Exception:
                pass
            self.character_page.detail_page.set_design_image_result(image_path)
            QMessageBox.information(self, "成功", "角色设计图生成完成！")

        def on_failed(error_msg: str):
            try:
                dialog.close()
            except Exception:
                pass
            self.character_page.detail_page.set_design_image_result("")
            QMessageBox.critical(self, "生成失败", f"AI 生成角色设计图失败：{error_msg}")

        def on_progress_update(text: str):
            status_label.setText(text)

        worker = CharacterDesignImageWorker(
            self._text_model_service,
            self._image_service,
            self._character_service,
            character,
            project_id,
        )
        worker.finished.connect(on_success)
        worker.failed.connect(on_failed)
        worker.progress_update.connect(on_progress_update)
        worker.start()

        # 保持引用避免被回收
        self._character_design_image_worker = worker

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

    def _on_task_finished(self, message_id: str, local_path: str, storyboard_id: int = 0) -> None:
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

    def _on_project_new_conversation(self, project_id: int) -> None:
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

    def _on_project_conversation_selected(self, project_id: int, conv_id: str) -> None:
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
            # 添加默认生成参数（如果 default_params 中未指定）
            params.setdefault("duration", 5)
            params.setdefault("prompt_extend", True)
            params.setdefault("watermark", False)

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
