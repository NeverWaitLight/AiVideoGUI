import unittest
from providers.dashscope_video import DashScopeVideoProvider
from models.provider_config import ProviderConfig


class TestDashScopeNewProtocol(unittest.TestCase):

    def setUp(self):
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            default_model="wan2.7-t2v",
        )
        self.provider = DashScopeVideoProvider(config)

    def test_basic_parameters_direct_pass_through(self):
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "duration": 10,
            "prompt_extend": True,
            "watermark": False,
        }

        payload = self.provider.build_payload("测试提示词", params)

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "测试提示词")

        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(payload["parameters"]["ratio"], "16:9")
        self.assertEqual(payload["parameters"]["duration"], 10)
        self.assertTrue(payload["parameters"]["prompt_extend"])
        self.assertFalse(payload["parameters"]["watermark"])

        self.assertNotIn("width", payload["parameters"])
        self.assertNotIn("height", payload["parameters"])

    def test_1080p_resolution(self):
        params = {
            "resolution": "1080P",
            "ratio": "9:16",
            "duration": 15,
        }

        payload = self.provider.build_payload("竖屏视频", params)

        self.assertEqual(payload["parameters"]["resolution"], "1080P")
        self.assertEqual(payload["parameters"]["ratio"], "9:16")
        self.assertEqual(payload["parameters"]["duration"], 15)
        self.assertNotIn("width", payload["parameters"])
        self.assertNotIn("height", payload["parameters"])

    def test_all_supported_ratios(self):
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]

        for ratio in ratios:
            params = {"resolution": "720P", "ratio": ratio}
            payload = self.provider.build_payload("测试", params)

            self.assertEqual(payload["parameters"]["ratio"], ratio)
            self.assertNotIn("width", payload["parameters"])
            self.assertNotIn("height", payload["parameters"])

    def test_negative_prompt_in_input(self):
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "negative_prompt": "低质量、模糊",
        }

        payload = self.provider.build_payload("高质量视频", params)

        self.assertEqual(payload["input"]["negative_prompt"], "低质量、模糊")

        self.assertNotIn("negative_prompt", payload["parameters"])

    def test_audio_url_in_input(self):
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "audio_url": "https://example.com/audio.mp3",
        }

        payload = self.provider.build_payload("配音视频", params)

        self.assertEqual(payload["input"]["audio_url"], "https://example.com/audio.mp3")

        self.assertNotIn("audio_url", payload["parameters"])

    def test_seed_in_parameters(self):
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "seed": 12345,
        }

        payload = self.provider.build_payload("可复现视频", params)

        self.assertEqual(payload["parameters"]["seed"], 12345)

    def test_combined_parameters(self):
        params = {
            "resolution": "1080P",
            "ratio": "16:9",
            "duration": 12,
            "prompt_extend": False,
            "watermark": True,
            "negative_prompt": "低分辨率",
            "audio_url": "https://example.com/bgm.mp3",
            "seed": 99999,
        }

        payload = self.provider.build_payload("完整参数测试", params)

        self.assertEqual(payload["input"]["prompt"], "完整参数测试")
        self.assertEqual(payload["input"]["negative_prompt"], "低分辨率")
        self.assertEqual(payload["input"]["audio_url"], "https://example.com/bgm.mp3")

        self.assertEqual(payload["parameters"]["resolution"], "1080P")
        self.assertEqual(payload["parameters"]["ratio"], "16:9")
        self.assertEqual(payload["parameters"]["duration"], 12)
        self.assertFalse(payload["parameters"]["prompt_extend"])
        self.assertTrue(payload["parameters"]["watermark"])
        self.assertEqual(payload["parameters"]["seed"], 99999)

        self.assertNotIn("width", payload["parameters"])
        self.assertNotIn("height", payload["parameters"])
        self.assertNotIn("negative_prompt", payload["parameters"])
        self.assertNotIn("audio_url", payload["parameters"])

    def test_empty_parameters(self):
        payload = self.provider.build_payload("仅提示词")

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "仅提示词")
        self.assertEqual(payload["parameters"], {})

    def test_none_parameters(self):
        payload = self.provider.build_payload("无参数", None)

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "无参数")
        self.assertEqual(payload["parameters"], {})

    def test_model_info_supported_resolutions(self):
        model_info_list = self.provider.get_model_info()

        self.assertEqual(len(model_info_list), 1)
        model_info = model_info_list[0]

        self.assertEqual(model_info.supported_resolutions, ["720P", "1080P"])

        self.assertEqual(
            model_info.supported_ratios, ["16:9", "9:16", "1:1", "4:3", "3:4"]
        )

        self.assertEqual(model_info.max_duration, 15)


if __name__ == "__main__":
    unittest.main()
