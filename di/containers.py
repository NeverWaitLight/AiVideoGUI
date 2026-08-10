from dependency_injector import containers, providers
from pathlib import Path
import os

from config.manager import ConfigManager
from prompts.manager import PromptTemplateManager
from prompts.chat_prompt_builder import ChatPromptBuilder
from service.background.enhanced_scheduler import BackgroundTaskScheduler
from service.background.video_polling_task import VideoTaskPollingTask
from service.character_service import CharacterService
from service.image_service import ImageService
from service.media_service import MediaService
from service.project_service import ProjectService
from service.screenplay_service import ScreenplayService
from service.story_outline_service import StoryOutlineService
from service.storyboard_service import StoryboardService
from service.chat_model_service import ChatModelService
from service.video_service import VideoService, _PROVIDER_REGISTRY
from service.visual_style_service import VisualStyleService
from service.update_service import UpdateService
from storage.session_manager import SessionManager
from prompts.video_prompt_builder import VideoPromptBuilder
from utils.ai_request_logger import AIRequestLogger


def _get_project_root() -> Path:
    return Path(__file__).parent.parent
class ApplicationContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    session_manager = providers.Singleton(
        SessionManager,
        workspace_root=config.workspace_root,
    )

    config_manager = providers.Singleton(
        ConfigManager,
        config_path=config.config_path,
    )

    video_prompt_builder = providers.Singleton(VideoPromptBuilder)

    prompt_template_manager = providers.Singleton(
        PromptTemplateManager,
        templates_dir=_get_project_root() / "prompts" / "templates",
    )

    text_prompt_builder = providers.Singleton(
        ChatPromptBuilder,
        template_manager=prompt_template_manager,
    )

    ai_request_logger = providers.Singleton(
        AIRequestLogger,
        config_manager=config_manager,
        workspace_root=config.workspace_root,
    )

    video_service = providers.Singleton(
        VideoService,
        session_manager=session_manager,
        config=config_manager,
        ai_request_logger=ai_request_logger,
    )

    media_service = providers.Singleton(
        MediaService,
        session_manager=session_manager,
        workspace_root=config.workspace_root,
    )

    project_service = providers.Singleton(
        ProjectService,
        session_manager=session_manager,
        workspace_root=config.workspace_root,
    )

    story_outline_service = providers.Singleton(
        StoryOutlineService,
        session_manager=session_manager,
    )

    screenplay_service = providers.Singleton(
        ScreenplayService,
        session_manager=session_manager,
    )

    storyboard_service = providers.Singleton(
        StoryboardService,
        session_mgr=session_manager,
        workspace_root=config.workspace_root,
    )

    character_service = providers.Singleton(
        CharacterService,
        session_manager=session_manager,
        workspace_root=config.workspace_root,
    )

    chat_model_service = providers.Singleton(
        ChatModelService,
        config_manager=config_manager,
        text_prompt_builder=text_prompt_builder,
        ai_request_logger=ai_request_logger,
    )

    image_service = providers.Singleton(
        ImageService,
        config_manager=config_manager,
        ai_request_logger=ai_request_logger,
    )

    visual_style_service = providers.Singleton(
        VisualStyleService,
        session_manager=session_manager,
    )

    background_scheduler = providers.Singleton(
        BackgroundTaskScheduler,
    )

    video_polling_task = providers.Singleton(
        VideoTaskPollingTask,
        session_manager=session_manager,
        provider_registry=providers.Object(_PROVIDER_REGISTRY),
        workspace_root=config.workspace_root,
        poll_interval=20.0,
        idle_check_interval=60.0,
        max_polls_per_task=150,
    )

    update_service = providers.Singleton(
        UpdateService,
        current_version=config.app_version,
        workspace_root=config.workspace_root,
    )

