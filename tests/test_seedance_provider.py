import unittest
from providers.seedance_video import SeedanceVideoProvider
from models.provider_config import ProviderConfig


class TestSeedanceProvider(unittest.TestCase):

    def setUp(self):
        config = ProviderConfig(
            provider_name="seedance",
            api_key="test-key",
            base_url="https://api.evolink.ai/v1",
            default_model="seedance-2.0-text-to-video",
        )
        self.provider = SeedanceVideoProvider(config)

    def test_build_payload_basic(self):
        params = {
            "duration": 8,
            "quality": "720p",
            "aspect_ratio": "16:9",
            "generate_audio": True,
        }

        payload = self.provider.build_payload("测试提示词", params)

        self.assertEqual(payload["model"], "seedance-2.0-text-to-video")
        self.assertEqual(payload["prompt"], "测试提示词")
        self.assertEqual(payload["duration"], 8)
        self.assertEqual(payload["quality"], "720p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertTrue(payload["generate_audio"])

    def test_build_payload_with_defaults(self):
        payload = self.provider.build_payload("简单提示词")

        self.assertEqual(payload["duration"], 5)
        self.assertEqual(payload["quality"], "720p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertTrue(payload["generate_audio"])

    def test_build_payload_all_quality_options(self):
        qualities = ["480p", "720p", "1080p", "4k"]

        for quality in qualities:
            params = {"quality": quality}
            payload = self.provider.build_payload("测试", params)
            self.assertEqual(payload["quality"], quality)

    def test_build_payload_all_aspect_ratios(self):
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"]

        for ratio in ratios:
            params = {"aspect_ratio": ratio}
            payload = self.provider.build_payload("测试", params)
            self.assertEqual(payload["aspect_ratio"], ratio)

    def test_build_payload_with_web_search(self):
        params = {
            "duration": 10,
            "quality": "1080p",
            "web_search": True,
        }

        payload = self.provider.build_payload("最新新闻视频", params)

        self.assertIn("model_params", payload)
        self.assertTrue(payload["model_params"]["web_search"])

    def test_build_payload_without_web_search(self):
        params = {
            "duration": 10,
            "quality": "1080p",
        }

        payload = self.provider.build_payload("普通视频", params)

        self.assertNotIn("model_params", payload)

    def test_build_payload_with_callback_url(self):
        params = {
            "duration": 5,
            "callback_url": "https://example.com/webhook",
        }

        payload = self.provider.build_payload("测试", params)

        self.assertEqual(payload["callback_url"], "https://example.com/webhook")

    def test_build_payload_disable_audio(self):
        params = {
            "generate_audio": False,
        }

        payload = self.provider.build_payload("无声视频", params)

        self.assertFalse(payload["generate_audio"])

    def test_model_info_seedance_20(self):
        model_info_list = self.provider.get_model_info()

        self.assertEqual(len(model_info_list), 1)
        model_info = model_info_list[0]

        self.assertEqual(
            model_info.supported_resolutions, ["480p", "720p", "1080p", "4k"]
        )

        self.assertEqual(
            model_info.supported_ratios,
            ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
        )

        self.assertEqual(model_info.max_duration, 15)

    def test_model_info_seedance_25(self):
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

        self.assertEqual(model_info.max_duration, 30)
        self.assertIn("2.5", model_info.description)

    def test_build_payload_combined_parameters(self):
        params = {
            "duration": 12,
            "quality": "4k",
            "aspect_ratio": "21:9",
            "generate_audio": False,
            "web_search": True,
            "callback_url": "https://example.com/callback",
        }

        payload = self.provider.build_payload("完整参数测试", params)

        self.assertEqual(payload["model"], "seedance-2.0-text-to-video")
        self.assertEqual(payload["prompt"], "完整参数测试")
        self.assertEqual(payload["duration"], 12)
        self.assertEqual(payload["quality"], "4k")
        self.assertEqual(payload["aspect_ratio"], "21:9")
        self.assertFalse(payload["generate_audio"])
        self.assertEqual(payload["callback_url"], "https://example.com/callback")

        self.assertIn("model_params", payload)
        self.assertTrue(payload["model_params"]["web_search"])


if __name__ == "__main__":
    unittest.main()
