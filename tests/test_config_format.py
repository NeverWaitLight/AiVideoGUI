import json
import os
import tempfile
import unittest

from config.manager import ConfigManager
from config.providers_catalog import ProvidersCatalog
from models.provider_config import ProviderConfig
from tests.test_providers_catalog import SAMPLE_CATALOG


class TestConfigFormat(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._catalog_path = os.path.join(self._tmpdir, "settings.json")
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CATALOG, f)
        self._catalog = ProvidersCatalog(self._catalog_path)

    def test_new_format_save_and_load_round_trip(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="deepseek",
                api_key="sk-chat",
                default_model="deepseek-v4-pro",
            ),
            provider_type="chat",
            auto_save=False,
        )
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-video",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )
        manager.save()

        with open(self._config_path, encoding="utf-8") as f:
            saved = json.load(f)

        self.assertEqual(saved["version"], 1)
        self.assertEqual(saved["chat"]["providers"][0]["id"], "deepseek")
        self.assertEqual(saved["video"]["providers"][0]["id"], "dashscope")
        self.assertNotIn("providers", saved)

        reloaded = ConfigManager(self._config_path, providers_catalog=self._catalog)
        chat_cfg = reloaded.get_provider("deepseek", "chat")
        video_cfg = reloaded.get_provider("dashscope", "video")
        assert chat_cfg is not None
        assert video_cfg is not None
        self.assertEqual(chat_cfg.api_key, "sk-chat")
        self.assertEqual(video_cfg.api_key, "sk-video")

    def test_legacy_deepseek_chat_migrates_to_new_format(self) -> None:
        legacy = {
            "providers": [
                {
                    "provider_name": "deepseek_chat",
                    "api_key": "sk-legacy",
                    "default_model": "deepseek-v4-pro",
                }
            ],
            "app_settings": {"default_chat_provider": "deepseek"},
        }
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(legacy, f)

        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = manager.get_provider("deepseek", "chat")
        assert cfg is not None
        self.assertEqual(cfg.api_key, "sk-legacy")
        self.assertEqual(cfg.provider_name, "deepseek")

        with open(self._config_path, encoding="utf-8") as f:
            migrated = json.load(f)
        self.assertEqual(migrated["chat"]["providers"][0]["id"], "deepseek")

    def test_same_id_independent_across_types(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(provider_name="dashscope", api_key="chat-key", default_model="qwen3.5-plus"),
            provider_type="chat",
            auto_save=False,
        )
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="video-key",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        chat_cfg = manager.get_provider("dashscope", "chat")
        video_cfg = manager.get_provider("dashscope", "video")
        assert chat_cfg is not None
        assert video_cfg is not None
        self.assertEqual(chat_cfg.api_key, "chat-key")
        self.assertEqual(video_cfg.api_key, "video-key")

    def test_config_without_base_url_uses_catalog_template(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        assert cfg is not None
        self.assertEqual(
            cfg.submit_base_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
        )

    def test_config_base_url_overrides_template_host(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                base_url="custom.example.com",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        assert cfg is not None
        self.assertIn("custom.example.com", cfg.submit_base_url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
