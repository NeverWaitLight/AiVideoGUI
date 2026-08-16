import json
import os
import tempfile
import unittest

from config.manager import ConfigManager
from config.providers_catalog import ProvidersCatalog
from models.provider_config import ProviderConfig


SAMPLE_CATALOG = {
    "version": 1,
    "chat": {
        "providers": [
            {
                "id": "dashscope",
                "name": "DashScope",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "models": ["qwen3.5-plus", "qwen3.5-flash"],
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com",
                "models": ["deepseek-v4-pro", "deepseek-v4-flash"],
            },
            {
                "id": "openai",
                "name": "OpenAI Compatible",
                "base_url": "",
                "models": [],
            },
        ]
    },
    "image": {
        "providers": [
            {
                "id": "dashscope",
                "name": "DashScope",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "t2i_models": ["wan2.6-t2i"],
                "i2i_models": ["wan2.6-t2i"],
                "r2i_models": ["wan2.6-t2i"],
            }
        ]
    },
    "video": {
        "providers": [
            {
                "id": "dashscope",
                "name": "DashScope",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "t2v_models": ["wan2.7-t2v-2026-06-12"],
                "i2v_models": ["wan2.7-i2v-2026-04-25"],
                "r2v_models": ["wan2.7-r2v-2026-06-12"],
            },
        ]
    },
}


class TestProvidersCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._catalog_path = os.path.join(self._tmpdir, "providers.json")
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CATALOG, f)

    def test_list_providers(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.list_providers("chat"),
            [
                {"id": "dashscope", "name": "DashScope"},
                {"id": "deepseek", "name": "DeepSeek"},
                {"id": "openai", "name": "OpenAI Compatible"},
            ],
        )
        self.assertEqual(
            catalog.list_providers("video"),
            [{"id": "dashscope", "name": "DashScope"}],
        )

    def test_list_provider_ids(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.list_provider_ids("chat"),
            ["dashscope", "deepseek", "openai"],
        )
        self.assertEqual(catalog.list_provider_ids("video"), ["dashscope"])

    def test_get_name(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(catalog.get_name("chat", "dashscope"), "DashScope")
        self.assertEqual(catalog.get_name("chat", "deepseek"), "DeepSeek")
        self.assertEqual(catalog.get_name("chat", "openai"), "OpenAI Compatible")
        self.assertEqual(catalog.get_name("video", "dashscope"), "DashScope")

    def test_get_base_url(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.get_base_url("chat", "dashscope"),
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.assertEqual(
            catalog.get_base_url("chat", "deepseek"),
            "https://api.deepseek.com",
        )
        self.assertEqual(catalog.get_base_url("chat", "openai"), "")
        self.assertEqual(
            catalog.get_base_url("video", "dashscope"),
            "https://dashscope.aliyuncs.com/api/v1",
        )

    def test_list_models(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.list_models("chat", "dashscope"),
            ["qwen3.5-plus", "qwen3.5-flash"],
        )
        self.assertEqual(
            catalog.list_models("chat", "deepseek"),
            ["deepseek-v4-pro", "deepseek-v4-flash"],
        )
        self.assertEqual(catalog.list_models("video", "dashscope"), [])

    def test_list_models_for_task(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.list_models_for_task("video", "dashscope", "t2v"),
            ["wan2.7-t2v-2026-06-12"],
        )
        self.assertEqual(
            catalog.list_models_for_task("video", "dashscope", "i2v"),
            ["wan2.7-i2v-2026-04-25"],
        )
        self.assertEqual(
            catalog.list_models_for_task("video", "dashscope", "r2v"),
            ["wan2.7-r2v-2026-06-12"],
        )
        self.assertEqual(
            catalog.list_models_for_task("image", "dashscope", "t2i"),
            ["wan2.6-t2i"],
        )
        self.assertEqual(
            catalog.list_models_for_task("image", "dashscope", "i2i"),
            ["wan2.6-t2i"],
        )
        self.assertEqual(
            catalog.list_models_for_task("image", "dashscope", "r2i"),
            ["wan2.6-t2i"],
        )


class TestConfigManagerCatalogIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._catalog_path = os.path.join(self._tmpdir, "providers.json")
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CATALOG, f)
        self._catalog = ProvidersCatalog(self._catalog_path)

    def test_resolve_fills_base_url_from_catalog(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope_video",
                api_key="sk-test",
                base_url="",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual(cfg.base_url, "https://dashscope.aliyuncs.com/api/v1")

    def test_validate_allows_empty_base_url_when_catalog_has_default(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = ProviderConfig(
            provider_name="dashscope",
            api_key="sk-test",
            base_url="",
            default_model="wan2.7-t2v-2026-06-12",
            model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
        )
        errors = manager.validate_provider_config(cfg, "video")
        self.assertNotIn("未设置 Base URL", errors)

    def test_validate_openai_chat_requires_base_url(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = ProviderConfig(
            provider_name="openai",
            api_key="sk-test",
            base_url="",
            default_model="gpt-4o",
        )
        errors = manager.validate_provider_config(cfg, "chat")
        self.assertIn("未设置 Base URL", errors)

        cfg.base_url = "https://example.com/v1"
        errors = manager.validate_provider_config(cfg, "chat")
        self.assertNotIn("未设置 Base URL", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
