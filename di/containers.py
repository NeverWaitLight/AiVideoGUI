"""依赖注入容器配置。

使用 dependency-injector 框架管理所有 Service 和 Repository 的依赖关系。
"""

from dependency_injector import containers, providers
from pathlib import Path
import os

from config.manager import ConfigManager
from prompts.manager import PromptTemplateManager
from service.background.enhanced_scheduler import BackgroundTaskScheduler
from service.background.video_polling_task import VideoTaskPollingTask
from service.background.project_cover_task import ProjectCoverGenerationTask
from service.character_service import CharacterService
from service.chat_service import ChatService
from service.image_service import ImageService
from service.media_service import MediaService
from service.project_service import ProjectService
from service.screenplay_service import ScreenplayService
from service.story_outline_service import StoryOutlineService
from service.storyboard_service import StoryboardService
from service.text_model_service import TextModelService
from service.video_service import VideoService, _PROVIDER_REGISTRY
from storage.session_manager import SessionManager
from utils.prompt_builder import VideoPromptBuilder


def _get_project_root() -> Path:
    """获取项目根目录（代码所在目录）。"""
    return Path(__file__).parent.parent
class ApplicationContainer(containers.DeclarativeContainer):
    """应用程序依赖注入容器。

    管理所有基础设施、Service、Repository 的生命周期和依赖关系。

    使用方式：
        # 初始化容器
        container = ApplicationContainer()
        container.config.workspace_root.from_value("C:/Users/admin/...")

        # 获取 Service 实例（自动注入依赖）
        video_service = container.video_service()
        project_service = container.project_service()
    """

    # ==================== 配置 ====================
    config = providers.Configuration()

    # ==================== 基础设施层 ====================

    # SessionManager（单例）
    session_manager = providers.Singleton(SessionManager)

    # ConfigManager（单例，需要 config_path）
    config_manager = providers.Singleton(
        ConfigManager,
        config_path=config.config_path,
    )

    # VideoPromptBuilder（单例）
    prompt_builder = providers.Singleton(VideoPromptBuilder)

    # PromptTemplateManager（单例）
    # 注意：模板文件位于项目代码目录下，不是用户数据目录
    prompt_template_manager = providers.Singleton(
        PromptTemplateManager,
        templates_dir=_get_project_root() / "prompts" / "templates",
    )

    # ==================== Service 层 ====================

    # VideoService（单例，注入 SessionManager 和 ConfigManager）
    video_service = providers.Singleton(
        VideoService,
        session_manager=session_manager,
        config=config_manager,
    )

    # MediaService（单例，注入 SessionManager 和 workspace_root）
    media_service = providers.Singleton(
        MediaService,
        session_manager=session_manager,
        workspace_root=config.workspace_root,
    )

    # ProjectService（单例，注入 SessionManager 和 workspace_root）
    project_service = providers.Singleton(
        ProjectService,
        session_manager=session_manager,
        workspace_root=config.workspace_root,
    )

    # StoryOutlineService（单例）
    story_outline_service = providers.Singleton(
        StoryOutlineService,
        session_manager=session_manager,
    )

    # ScreenplayService（单例）
    screenplay_service = providers.Singleton(
        ScreenplayService,
        session_manager=session_manager,
    )

    # StoryboardService（单例）
    storyboard_service = providers.Singleton(
        StoryboardService,
        session_mgr=session_manager,
    )

    # CharacterService（单例）
    character_service = providers.Singleton(
        CharacterService,
        session_manager=session_manager,
    )

    # ChatService（单例）
    chat_service = providers.Singleton(
        ChatService,
        config=config_manager,
    )

    # TextModelService（单例）
    text_model_service = providers.Singleton(
        TextModelService,
        config_manager=config_manager,
        prompt_manager=prompt_template_manager,
    )

    # ImageService（单例）
    image_service = providers.Singleton(
        ImageService,
        config_manager=config_manager,
    )

    # ==================== 后台任务调度器 ====================

    # 后台任务调度器（单例）
    background_scheduler = providers.Singleton(
        BackgroundTaskScheduler,
    )

    # 视频任务轮询任务（单例，周期性任务）
    video_polling_task = providers.Singleton(
        VideoTaskPollingTask,
        session_manager=session_manager,
        provider_registry=providers.Object(_PROVIDER_REGISTRY),
        workspace_root=config.workspace_root,
        poll_interval=10.0,
        idle_check_interval=60.0,
        max_polls_per_task=150,
    )

    # 项目封面生成任务（单例，一次性任务）
    project_cover_task = providers.Singleton(
        ProjectCoverGenerationTask,
        session_manager=session_manager,
        image_service=image_service,
        workspace_root=config.workspace_root,
    )

