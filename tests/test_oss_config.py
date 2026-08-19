import json
import os
import tempfile
import unittest

from config.providers_catalog import ProvidersCatalog


class TestOssConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._catalog_path = os.path.join(self._tmpdir, "settings.json")

    def test_loads_explicit_oss_section(self) -> None:
        catalog_data = {
            "video": {
                "providers": [
                    {
                        "id": "dashscope",
                        "name": "DashScope",
                        "submit_base_url": "https://example.com/submit",
                        "task_base_url": "https://example.com/tasks",
                    }
                ]
            },
            "oss": {
                "providers": [
                    {
                        "id": "dashscope",
                        "name": "DashScope OSS",
                        "get_policy_url": "https://example.com/uploads",
                        "get_policy_params": {"action": "getPolicy"},
                    }
                ]
            },
        }
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f)

        catalog = ProvidersCatalog(self._catalog_path)
        oss = catalog.get_oss_config("dashscope")
        self.assertIsNotNone(oss)
        assert oss is not None
        self.assertEqual(oss.get_policy_url, "https://example.com/uploads")
        self.assertEqual(oss.get_policy_params, {"action": "getPolicy"})

    def test_fallback_oss_url_from_legacy_video_base_url(self) -> None:
        catalog_data = {
            "video": {
                "providers": [
                    {
                        "id": "dashscope",
                        "name": "DashScope",
                        "base_url": "https://example.com/api/v1",
                    }
                ]
            }
        }
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f)

        catalog = ProvidersCatalog(self._catalog_path)
        oss = catalog.get_oss_config("dashscope")
        self.assertIsNotNone(oss)
        assert oss is not None
        self.assertEqual(oss.get_policy_url, "https://example.com/api/v1/uploads")
        self.assertEqual(oss.get_policy_params, {"action": "getPolicy"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
