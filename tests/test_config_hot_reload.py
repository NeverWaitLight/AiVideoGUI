import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from config.manager import ConfigManager
from config.providers_catalog import ProvidersCatalog
from models.provider_config import ProviderConfig
from service.background.video_polling_task import VideoTaskPollingTask
from service.chat_service import ChatService
from service.video_service import VideoService
from tests.test_providers_catalog import SAMPLE_CATALOG


class _RecordingChatProvider:
    instances: list["_RecordingChatProvider"] = []

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        _RecordingChatProvider.instances.append(self)


class _RecordingVideoProvider:
    instances: list["_RecordingVideoProvider"] = []

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        _RecordingVideoProvider.instances.append(self)

    def set_session_manager(self, _session_manager) -> None:
        pass


class TestConfigHotReload(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._catalog_path = os.path.join(self._tmpdir, "settings.json")
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CATALOG, f)
        self._catalog = ProvidersCatalog(self._catalog_path)
        self._manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        self._manager.update_settings(
            auto_save=False,
            default_chat_provider="dashscope",
            default_provider="dashscope",
        )
        self._manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_chat",
                api_key="old-chat-key",
                default_model="qwen3.5-plus",
            ),
            auto_save=False,
        )
        self._manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_video",
                api_key="old-video-key",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            auto_save=False,
        )

    @patch("service.chat_service._PROVIDER_REGISTRY", {"dashscope": _RecordingChatProvider})
    def test_chat_service_rebuilds_provider_after_invalidate(self) -> None:
        _RecordingChatProvider.instances.clear()
        service = ChatService(
            config_manager=self._manager,
            session_manager=MagicMock(),
            text_prompt_builder=MagicMock(),
        )

        first = service._get_provider()
        self.assertEqual(first.config.api_key, "old-chat-key")

        self._manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_chat",
                api_key="new-chat-key",
                default_model="qwen3.5-plus",
            ),
            auto_save=False,
        )
        service.invalidate_provider_cache()
        second = service._get_provider()

        self.assertIsNot(first, second)
        self.assertEqual(second.config.api_key, "new-chat-key")
        self.assertEqual(len(_RecordingChatProvider.instances), 2)

    @patch("service.video_service._PROVIDER_REGISTRY", {"dashscope": _RecordingVideoProvider})
    def test_video_service_rebuilds_provider_after_invalidate(self) -> None:
        _RecordingVideoProvider.instances.clear()
        service = VideoService(
            session_manager=MagicMock(),
            config=self._manager,
            chat_service=MagicMock(),
            prompt_builder=MagicMock(),
            storyboard_service=MagicMock(),
            screenplay_service=MagicMock(),
            workspace_root=self._tmpdir,
        )

        first = service.get_provider("dashscope")
        self.assertEqual(first.config.api_key, "old-video-key")

        self._manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_video",
                api_key="new-video-key",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            auto_save=False,
        )
        service.invalidate_provider_cache()
        second = service.get_provider("dashscope")

        self.assertIsNot(first, second)
        self.assertEqual(second.config.api_key, "new-video-key")
        self.assertEqual(len(_RecordingVideoProvider.instances), 2)

    def test_video_polling_task_rebuilds_provider_after_invalidate(self) -> None:
        _RecordingVideoProvider.instances.clear()
        registry = {"dashscope": _RecordingVideoProvider}
        task = VideoTaskPollingTask(
            session_manager=MagicMock(),
            provider_registry=registry,
            workspace_root=self._tmpdir,
        )
        task.set_config_manager(self._manager)

        first = task.get_provider("dashscope")
        self.assertEqual(first.config.api_key, "old-video-key")

        self._manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_video",
                api_key="new-polling-key",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            auto_save=False,
        )
        task.invalidate_provider_cache()
        second = task.get_provider("dashscope")

        self.assertIsNot(first, second)
        self.assertEqual(second.config.api_key, "new-polling-key")

    def test_app_bridge_on_settings_saved_invalidates_all_caches(self) -> None:
        chat_service = MagicMock()
        video_service = MagicMock()
        image_service = MagicMock()
        video_polling_task = MagicMock()

        from bridge.app_bridge import AppBridge

        bridge = AppBridge.__new__(AppBridge)
        bridge._text_model_service = chat_service
        bridge._video_service = video_service
        bridge._image_service = image_service
        bridge._video_polling_task = video_polling_task

        bridge._on_settings_saved()

        chat_service.invalidate_provider_cache.assert_called_once()
        video_service.invalidate_provider_cache.assert_called_once()
        image_service.invalidate_provider_cache.assert_called_once()
        video_polling_task.invalidate_provider_cache.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
