import json
import os
import tempfile
import unittest

from config.manager import ConfigManager
from config.providers_catalog import ProvidersCatalog
from models.oss_config import OssConfig
from models.provider_config import ProviderConfig


SAMPLE_OSS = OssConfig(
    provider_id="dashscope",
    get_policy_url="https://dashscope.aliyuncs.com/api/v1/uploads",
    get_policy_params={"action": "getPolicy"},
)

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
                "base_url": "https://{base_url:dashscope.aliyuncs.com}/api/v1/services/aigc/multimodal-generation/generation",
                "t2i_models": ["wan2.6-t2i"],
            }
        ]
    },
    "video": {
        "providers": [
            {
                "id": "dashscope",
                "name": "DashScope",
                "submit_base_url": "https://{base_url:dashscope.aliyuncs.com}/api/v1/services/aigc/video-generation/video-synthesis",
                "task_base_url": "https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks",
                "t2v_models": ["wan2.7-t2v-2026-06-12"],
                "i2v_models": ["wan2.7-i2v-2026-04-25"],
                "r2v_models": ["wan2.7-r2v-2026-06-12"],
            },
        ]
    },
    "oss": {
        "providers": [
            {
                "id": "dashscope",
                "name": "DashScope OSS",
                "get_policy_url": "https://dashscope.aliyuncs.com/api/v1/uploads",
                "get_policy_params": {"action": "getPolicy"},
            }
        ]
    },
    "update": {
        "github_repo": "NeverWaitLight/AiVideoGUI",
        "github_api_url": "https://api.github.com/repos/NeverWaitLight/AiVideoGUI/releases/latest",
    },
}


def make_video_config(**overrides) -> ProviderConfig:
    data = {
        "provider_name": "dashscope",
        "api_key": "test-key",
        "submit_base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
        "task_base_url": "https://dashscope.aliyuncs.com/api/v1/tasks",
        "default_model": "wan2.7-t2v",
        "model_mappings": {
            "t2v": "wan2.7-t2v-2026-06-12",
            "i2v": "wan2.7-i2v-2026-04-25",
            "r2v": "wan2.7-r2v-2026-06-12",
        },
        "oss": SAMPLE_OSS,
    }
    data.update(overrides)
    return ProviderConfig(**data)


class TestProvidersCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._catalog_path = os.path.join(self._tmpdir, "settings.json")
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
            "https://{base_url:dashscope.aliyuncs.com}/api/v1/services/aigc/video-generation/video-synthesis",
        )
        self.assertEqual(
            catalog.get_base_url("image", "dashscope"),
            "https://{base_url:dashscope.aliyuncs.com}/api/v1/services/aigc/multimodal-generation/generation",
        )

    def test_get_base_url_default(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.get_base_url_default("video", "dashscope"),
            "dashscope.aliyuncs.com",
        )
        self.assertEqual(
            catalog.get_base_url_default("image", "dashscope"),
            "dashscope.aliyuncs.com",
        )
        self.assertEqual(
            catalog.get_base_url_default("chat", "dashscope"),
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def test_get_task_base_url(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(
            catalog.get_task_base_url("dashscope"),
            "https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks",
        )

    def test_get_oss_config(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        oss = catalog.get_oss_config("dashscope")
        self.assertIsNotNone(oss)
        assert oss is not None
        self.assertEqual(
            oss.get_policy_url,
            "https://dashscope.aliyuncs.com/api/v1/uploads",
        )
        self.assertEqual(oss.get_policy_params, {"action": "getPolicy"})

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

    def test_get_update_config(self) -> None:
        catalog = ProvidersCatalog(self._catalog_path)
        self.assertEqual(catalog.get_update_github_repo(), "NeverWaitLight/AiVideoGUI")
        self.assertEqual(
            catalog.get_update_github_api_url(),
            "https://api.github.com/repos/NeverWaitLight/AiVideoGUI/releases/latest",
        )


class TestConfigManagerCatalogIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._catalog_path = os.path.join(self._tmpdir, "settings.json")
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CATALOG, f)
        self._catalog = ProvidersCatalog(self._catalog_path)

    def test_resolve_fills_video_urls_from_catalog(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual(
            cfg.submit_base_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
        )
        self.assertEqual(cfg.task_base_url, "https://dashscope.aliyuncs.com/api/v1/tasks")
        self.assertIsNotNone(cfg.oss)

    def test_user_host_overrides_both_video_urls(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                base_url="custom.example.com",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        assert cfg is not None
        self.assertEqual(
            cfg.submit_base_url,
            "https://custom.example.com/api/v1/services/aigc/video-generation/video-synthesis",
        )
        self.assertEqual(cfg.task_base_url, "https://custom.example.com/api/v1/tasks")

    def test_user_host_with_https_prefix_is_normalized(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                base_url="https://custom.example.com/",
                default_model="wan2.7-t2v-2026-06-12",
                model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
            ),
            provider_type="video",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "video")
        assert cfg is not None
        self.assertEqual(
            cfg.submit_base_url,
            "https://custom.example.com/api/v1/services/aigc/video-generation/video-synthesis",
        )

    def test_image_url_resolved_from_template(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        manager.upsert_provider(
            ProviderConfig(
                provider_name="dashscope",
                api_key="sk-test",
                base_url="custom.example.com",
            ),
            provider_type="image",
            auto_save=False,
        )

        cfg = manager.get_provider_config("dashscope", "image")
        assert cfg is not None
        self.assertEqual(
            cfg.base_url,
            "https://custom.example.com/api/v1/services/aigc/multimodal-generation/generation",
        )

    def test_validate_allows_empty_submit_when_catalog_has_default(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = ProviderConfig(
            provider_name="dashscope",
            api_key="sk-test",
            default_model="wan2.7-t2v-2026-06-12",
            model_mappings={"t2v": "wan2.7-t2v-2026-06-12"},
        )
        errors = manager.validate_provider_config(cfg, "video")
        self.assertNotIn("未设置 Base URL", errors)

    def test_validate_video_accepts_model_mappings_without_default_model(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = ProviderConfig(
            provider_name="dashscope",
            api_key="sk-test",
            model_mappings={
                "t2v": "wan2.7-t2v-2026-06-12",
                "i2v": "wan2.7-i2v-2026-04-25",
            },
        )
        errors = manager.validate_provider_config(cfg, "video")
        self.assertNotIn("未选择默认模型", errors)
        self.assertNotIn("未配置模型映射（model_mappings）或默认模型（default_model）", errors)

    def test_validate_image_accepts_catalog_fallback_model(self) -> None:
        manager = ConfigManager(self._config_path, providers_catalog=self._catalog)
        cfg = ProviderConfig(
            provider_name="dashscope",
            api_key="sk-test",
        )
        errors = manager.validate_provider_config(cfg, "image")
        self.assertNotIn("未选择默认模型", errors)

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
