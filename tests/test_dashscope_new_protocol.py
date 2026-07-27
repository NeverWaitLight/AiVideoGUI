"""测试 DashScope Provider 新版 wan2.7 API 协议参数映射。"""

import unittest
from providers.dashscope_video import DashScopeVideoProvider
from models.data_models import ProviderConfig


class TestDashScopeNewProtocol(unittest.TestCase):
    """测试新版 API 协议的参数映射逻辑。"""

    def setUp(self):
        """初始化测试 Provider。"""
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            default_model="wan2.7-t2v",
        )
        self.provider = DashScopeVideoProvider(config)

    def test_basic_parameters_direct_pass_through(self):
        """测试基本参数直接传递，不转换为 width/height。"""
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "duration": 10,
            "prompt_extend": True,
            "watermark": False,
        }

        payload = self.provider.build_payload("测试提示词", params)

        # 验证结构
        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "测试提示词")

        # 验证参数直接传递，无转换
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(payload["parameters"]["ratio"], "16:9")
        self.assertEqual(payload["parameters"]["duration"], 10)
        self.assertTrue(payload["parameters"]["prompt_extend"])
        self.assertFalse(payload["parameters"]["watermark"])

        # 验证不存在旧协议的 width/height
        self.assertNotIn("width", payload["parameters"])
        self.assertNotIn("height", payload["parameters"])

    def test_1080p_resolution(self):
        """测试 1080P 分辨率参数。"""
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
        """测试所有支持的宽高比。"""
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]

        for ratio in ratios:
            params = {"resolution": "720P", "ratio": ratio}
            payload = self.provider.build_payload("测试", params)

            self.assertEqual(payload["parameters"]["ratio"], ratio)
            self.assertNotIn("width", payload["parameters"])
            self.assertNotIn("height", payload["parameters"])

    def test_negative_prompt_in_input(self):
        """测试 negative_prompt 被正确添加到 input 对象。"""
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "negative_prompt": "低质量、模糊",
        }

        payload = self.provider.build_payload("高质量视频", params)

        # negative_prompt 应该在 input 中
        self.assertEqual(payload["input"]["negative_prompt"], "低质量、模糊")

        # 不应该在 parameters 中
        self.assertNotIn("negative_prompt", payload["parameters"])

    def test_audio_url_in_input(self):
        """测试 audio_url 被正确添加到 input 对象。"""
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "audio_url": "https://example.com/audio.mp3",
        }

        payload = self.provider.build_payload("配音视频", params)

        # audio_url 应该在 input 中
        self.assertEqual(payload["input"]["audio_url"], "https://example.com/audio.mp3")

        # 不应该在 parameters 中
        self.assertNotIn("audio_url", payload["parameters"])

    def test_seed_in_parameters(self):
        """测试 seed 参数保留在 parameters 中。"""
        params = {
            "resolution": "720P",
            "ratio": "16:9",
            "seed": 12345,
        }

        payload = self.provider.build_payload("可复现视频", params)

        # seed 应该在 parameters 中
        self.assertEqual(payload["parameters"]["seed"], 12345)

    def test_combined_parameters(self):
        """测试所有参数组合。"""
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

        # 验证 input 对象
        self.assertEqual(payload["input"]["prompt"], "完整参数测试")
        self.assertEqual(payload["input"]["negative_prompt"], "低分辨率")
        self.assertEqual(payload["input"]["audio_url"], "https://example.com/bgm.mp3")

        # 验证 parameters 对象
        self.assertEqual(payload["parameters"]["resolution"], "1080P")
        self.assertEqual(payload["parameters"]["ratio"], "16:9")
        self.assertEqual(payload["parameters"]["duration"], 12)
        self.assertFalse(payload["parameters"]["prompt_extend"])
        self.assertTrue(payload["parameters"]["watermark"])
        self.assertEqual(payload["parameters"]["seed"], 99999)

        # 验证不存在旧协议字段
        self.assertNotIn("width", payload["parameters"])
        self.assertNotIn("height", payload["parameters"])
        self.assertNotIn("negative_prompt", payload["parameters"])
        self.assertNotIn("audio_url", payload["parameters"])

    def test_empty_parameters(self):
        """测试空参数字典。"""
        payload = self.provider.build_payload("仅提示词")

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "仅提示词")
        self.assertEqual(payload["parameters"], {})

    def test_none_parameters(self):
        """测试 None 参数。"""
        payload = self.provider.build_payload("无参数", None)

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "无参数")
        self.assertEqual(payload["parameters"], {})

    def test_model_info_supported_resolutions(self):
        """测试模型信息返回正确的分辨率支持列表。"""
        model_info_list = self.provider.get_model_info()

        self.assertEqual(len(model_info_list), 1)
        model_info = model_info_list[0]

        # 验证仅支持 720P 和 1080P
        self.assertEqual(model_info.supported_resolutions, ["720P", "1080P"])

        # 验证支持所有5种宽高比
        self.assertEqual(
            model_info.supported_ratios, ["16:9", "9:16", "1:1", "4:3", "3:4"]
        )

        # 验证最大时长
        self.assertEqual(model_info.max_duration, 15)


if __name__ == "__main__":
    unittest.main()
