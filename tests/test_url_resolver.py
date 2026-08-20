import unittest

from config.url_resolver import (
    extract_url_variable_default,
    get_chat_base_url,
    get_image_url,
    get_oss_policy_params,
    get_oss_policy_url,
    get_task_base_url,
    get_video_submit_url,
    has_url_template,
    normalize_host,
    resolve_url_template,
)
from models.oss_config import OssConfig
from models.provider_config import ProviderConfig


class TestUrlResolver(unittest.TestCase):
    def test_get_image_url(self) -> None:
        cfg = ProviderConfig(
            provider_name="dashscope_image",
            base_url="https://example.com/image/generation",
        )
        self.assertEqual(get_image_url(cfg), "https://example.com/image/generation")

    def test_get_video_submit_url_prefers_submit_base_url(self) -> None:
        cfg = ProviderConfig(
            provider_name="dashscope",
            base_url="https://example.com/legacy",
            submit_base_url="https://example.com/video/submit",
        )
        self.assertEqual(get_video_submit_url(cfg), "https://example.com/video/submit")

    def test_get_video_submit_url_falls_back_to_base_url(self) -> None:
        cfg = ProviderConfig(
            provider_name="dashscope",
            base_url="https://example.com/legacy",
        )
        self.assertEqual(get_video_submit_url(cfg), "https://example.com/legacy")

    def test_get_task_base_url(self) -> None:
        cfg = ProviderConfig(
            provider_name="dashscope",
            task_base_url="https://example.com/tasks",
        )
        self.assertEqual(get_task_base_url(cfg), "https://example.com/tasks")

    def test_get_chat_base_url(self) -> None:
        cfg = ProviderConfig(
            provider_name="dashscope",
            base_url="https://example.com/compatible-mode/v1/",
        )
        self.assertEqual(get_chat_base_url(cfg), "https://example.com/compatible-mode/v1")

    def test_get_oss_policy(self) -> None:
        oss = OssConfig(
            provider_id="dashscope",
            get_policy_url="https://example.com/uploads/",
            get_policy_params={"action": "getPolicy"},
        )
        self.assertEqual(get_oss_policy_url(oss), "https://example.com/uploads")
        self.assertEqual(get_oss_policy_params(oss), {"action": "getPolicy"})

    def test_has_url_template(self) -> None:
        self.assertTrue(
            has_url_template("https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks")
        )
        self.assertFalse(has_url_template("https://dashscope.aliyuncs.com/api/v1/tasks"))

    def test_extract_url_variable_default(self) -> None:
        url = "https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks"
        self.assertEqual(extract_url_variable_default(url), "dashscope.aliyuncs.com")
        self.assertEqual(extract_url_variable_default(url, "other"), "")

    def test_normalize_host(self) -> None:
        self.assertEqual(normalize_host("dashscope.aliyuncs.com"), "dashscope.aliyuncs.com")
        self.assertEqual(
            normalize_host("https://custom.example.com/"),
            "custom.example.com",
        )

    def test_resolve_url_template_with_user_host(self) -> None:
        template = "https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks"
        self.assertEqual(
            resolve_url_template(template, {"base_url": "custom.example.com"}),
            "https://custom.example.com/api/v1/tasks",
        )

    def test_resolve_url_template_uses_default_when_empty(self) -> None:
        template = "https://{base_url:dashscope.aliyuncs.com}/api/v1/tasks"
        self.assertEqual(
            resolve_url_template(template, {"base_url": ""}),
            "https://dashscope.aliyuncs.com/api/v1/tasks",
        )
        self.assertEqual(
            resolve_url_template(template, {"base_url": None}),
            "https://dashscope.aliyuncs.com/api/v1/tasks",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
