"""测试配置验证功能的演示脚本"""
import unittest
from models.provider_config import ProviderConfig
from models.exceptions import MissingConfigError
from providers.dashscope_video import DashScopeVideoProvider
from tests.test_providers_catalog import make_video_config


class TestConfigValidation(unittest.TestCase):
    """验证配置验证功能"""

    def test_valid_config_succeeds(self):
        """测试完整配置可以成功创建 Provider"""
        config = make_video_config(
            api_key="sk-test-key",
            default_model="wan2.7-t2v",
        )
        provider = DashScopeVideoProvider(config)
        self.assertIsNotNone(provider)
        self.assertEqual(
            provider._submit_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
        )
        self.assertEqual(provider._model, "wan2.7-t2v")

    def test_missing_config_shows_helpful_error(self):
        """测试缺失配置时显示友好的错误消息"""
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="",
            default_model="",
            model_mappings={}
        )

        with self.assertRaises(MissingConfigError) as ctx:
            DashScopeVideoProvider(config)

        error = ctx.exception

        self.assertIn("api_key", str(error))
        self.assertIn("submit_base_url", str(error))
        self.assertIn("model_mappings", str(error))

        self.assertIn("请在设置中配置以下字段", str(error))
        self.assertIn("DashScope 视频生成服务", str(error))

        print("\n" + "="*60)
        print("配置缺失错误示例：")
        print("="*60)
        print(str(error))
        print("="*60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
