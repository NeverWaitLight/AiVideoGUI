"""测试 Seedance Provider 的参数映射和 API 调用。"""

import unittest
from providers.seedance_video import SeedanceVideoProvider
from models.provider_config import ProviderConfig


class TestSeedanceProvider(unittest.TestCase):
    """测试 Seedance Provider 的基本功能。"""

    def setUp(self):
        """初始化测试 Provider。"""
        config = ProviderConfig(
            provider_name="seedance",
            api_key="test-key",
            base_url="https://api.evolink.ai/v1",
            default_model="seedance-2.0-text-to-video",
        )
        self.provider = SeedanceVideoProvider(config)

    def test_build_payload_basic(self):
        """测试基本参数构建。"""
        params = {
            "duration": 8,
            "quality": "720p",
            "aspect_ratio": "16:9",
            "generate_audio": True,
        }

        payload = self.provider.build_payload("测试提示词", params)

        # 验证结构
        self.assertEqual(payload["model"], "seedance-2.0-text-to-video")
        self.assertEqual(payload["prompt"], "测试提示词")
        self.assertEqual(payload["duration"], 8)
        self.assertEqual(payload["quality"], "720p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertTrue(payload["generate_audio"])

    def test_build_payload_with_defaults(self):
        """测试默认参数。"""
        payload = self.provider.build_payload("简单提示词")

        self.assertEqual(payload["duration"], 5)
        self.assertEqual(payload["quality"], "720p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertTrue(payload["generate_audio"])

    def test_build_payload_all_quality_options(self):
        """测试所有画质选项。"""
        qualities = ["480p", "720p", "1080p", "4k"]

        for quality in qualities:
            params = {"quality": quality}
            payload = self.provider.build_payload("测试", params)
            self.assertEqual(payload["quality"], quality)

    def test_build_payload_all_aspect_ratios(self):
        """测试所有宽高比。"""
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"]

        for ratio in ratios:
            params = {"aspect_ratio": ratio}
            payload = self.provider.build_payload("测试", params)
            self.assertEqual(payload["aspect_ratio"], ratio)

    def test_build_payload_with_web_search(self):
        """测试联网检索参数。"""
        params = {
            "duration": 10,
            "quality": "1080p",
            "web_search": True,
        }

        payload = self.provider.build_payload("最新新闻视频", params)

        # 验证 model_params 嵌套
        self.assertIn("model_params", payload)
        self.assertTrue(payload["model_params"]["web_search"])

    def test_build_payload_without_web_search(self):
        """测试不带联网检索参数时不生成 model_params。"""
        params = {
            "duration": 10,
            "quality": "1080p",
        }

        payload = self.provider.build_payload("普通视频", params)

        # 验证没有 model_params
        self.assertNotIn("model_params", payload)

    def test_build_payload_with_callback_url(self):
        """测试回调 URL 参数。"""
        params = {
            "duration": 5,
            "callback_url": "https://example.com/webhook",
        }

        payload = self.provider.build_payload("测试", params)

        self.assertEqual(payload["callback_url"], "https://example.com/webhook")

    def test_build_payload_disable_audio(self):
        """测试禁用音频生成。"""
        params = {
            "generate_audio": False,
        }

        payload = self.provider.build_payload("无声视频", params)

        self.assertFalse(payload["generate_audio"])

    def test_model_info_seedance_20(self):
        """测试 Seedance 2.0 的模型信息。"""
        model_info_list = self.provider.get_model_info()

        self.assertEqual(len(model_info_list), 1)
        model_info = model_info_list[0]

        # 验证支持的画质
        self.assertEqual(
            model_info.supported_resolutions, ["480p", "720p", "1080p", "4k"]
        )

        # 验证支持的宽高比
        self.assertEqual(
            model_info.supported_ratios,
            ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
        )

        # 验证最大时长（2.0 支持 4-15 秒）
        self.assertEqual(model_info.max_duration, 15)

    def test_model_info_seedance_25(self):
        """测试 Seedance 2.5 的模型信息（模拟）。"""
        config = ProviderConfig(
            provider_name="seedance",
            api_key="test-key",
            base_url="https://api.evolink.ai/v1",
            default_model="seedance-2.5-text-to-video",
        )
        provider = SeedanceVideoProvider(config)

        model_info_list = provider.get_model_info()

        self.assertEqual(len(model_info_list), 1)
        model_info = model_info_list[0]

        # 验证最大时长（2.5 支持 30 秒）
        self.assertEqual(model_info.max_duration, 30)
        self.assertIn("2.5", model_info.description)

    def test_build_payload_combined_parameters(self):
        """测试所有参数组合。"""
        params = {
            "duration": 12,
            "quality": "4k",
            "aspect_ratio": "21:9",
            "generate_audio": False,
            "web_search": True,
            "callback_url": "https://example.com/callback",
        }

        payload = self.provider.build_payload("完整参数测试", params)

        # 验证顶层字段
        self.assertEqual(payload["model"], "seedance-2.0-text-to-video")
        self.assertEqual(payload["prompt"], "完整参数测试")
        self.assertEqual(payload["duration"], 12)
        self.assertEqual(payload["quality"], "4k")
        self.assertEqual(payload["aspect_ratio"], "21:9")
        self.assertFalse(payload["generate_audio"])
        self.assertEqual(payload["callback_url"], "https://example.com/callback")

        # 验证 model_params
        self.assertIn("model_params", payload)
        self.assertTrue(payload["model_params"]["web_search"])


if __name__ == "__main__":
    unittest.main()
