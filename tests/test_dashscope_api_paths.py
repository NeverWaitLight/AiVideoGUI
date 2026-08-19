import unittest

from models.oss_config import OssConfig
from models.provider_config import ProviderConfig
from providers.dashscope_image import DashScopeImageProvider
from providers.dashscope_oss_uploader import DashScopeOSSUploader
from providers.dashscope_video import DashScopeVideoProvider
from tests.test_providers_catalog import SAMPLE_OSS, make_video_config


class TestDashScopeApiPaths(unittest.TestCase):
    def test_image_provider_uses_configured_base_url(self) -> None:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        provider = DashScopeImageProvider(
            ProviderConfig(provider_name="dashscope_image", api_key="sk-test", base_url=url)
        )
        self.assertEqual(provider.submit_url, url)

    def test_video_provider_uses_configured_urls(self) -> None:
        provider = DashScopeVideoProvider(make_video_config())
        self.assertEqual(
            provider._submit_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
        )
        self.assertEqual(provider._task_url, "https://dashscope.aliyuncs.com/api/v1/tasks")

    def test_oss_uploader_uses_configured_policy_url(self) -> None:
        uploader = DashScopeOSSUploader("sk-test", oss_config=SAMPLE_OSS)
        self.assertEqual(
            uploader._policy_api_url,
            "https://dashscope.aliyuncs.com/api/v1/uploads",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
