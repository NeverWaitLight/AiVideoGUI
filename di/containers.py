from dependency_injector import containers, providers
from pathlib import Path
import os

from config.manager import ConfigManager
from prompts.manager import PromptTemplateManager
from service.background.enhanced_scheduler import BackgroundTaskScheduler
from service.background.video_polling_task import VideoTaskPollingTask
from service.character_service import CharacterService
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

    prompt_builder = providers.Singleton(VideoPromptBuilder)

    prompt_template_manager = providers.Singleton(
        PromptTemplateManager,
        templates_dir=_get_project_root() / "prompts" / "templates",
    )

    video_service = providers.Singleton(
        VideoService,
        session_manager=session_manager,
        config=config_manager,
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

    text_model_service = providers.Singleton(
        TextModelService,
        config_manager=config_manager,
        prompt_manager=prompt_template_manager,
    )

    image_service = providers.Singleton(
        ImageService,
        config_manager=config_manager,
    )

    background_scheduler = providers.Singleton(
        BackgroundTaskScheduler,
    )

    video_polling_task = providers.Singleton(
        VideoTaskPollingTask,
        session_manager=session_manager,
        provider_registry=providers.Object(_PROVIDER_REGISTRY),
        workspace_root=config.workspace_root,
        poll_interval=10.0,
        idle_check_interval=60.0,
        max_polls_per_task=150,
    )

