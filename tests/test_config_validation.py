"""测试配置验证功能的演示脚本"""
import unittest
from models.provider_config import ProviderConfig
from models.exceptions import MissingConfigError
from providers.dashscope_video import DashScopeVideoProvider


class TestConfigValidation(unittest.TestCase):
    """验证配置验证功能"""

    def test_valid_config_succeeds(self):
        """测试完整配置可以成功创建 Provider"""
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="sk-test-key",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            default_model="wan2.7-t2v",
            model_mappings={
                "t2v": "wan2.7-t2v-2026-06-12",
                "i2v": "wan2.7-i2v-2026-04-25",
                "r2v": "wan2.7-r2v-2026-06-12"
            }
        )
        provider = DashScopeVideoProvider(config)
        self.assertIsNotNone(provider)
        self.assertEqual(provider._base_url, "https://dashscope.aliyuncs.com/api/v1")
        self.assertEqual(provider._model, "wan2.7-t2v")

    def test_missing_config_shows_helpful_error(self):
        """测试缺失配置时显示友好的错误消息"""
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="",
            base_url="",
            default_model="",
            model_mappings={}
        )

        with self.assertRaises(MissingConfigError) as ctx:
            DashScopeVideoProvider(config)

        error = ctx.exception

        # 验证错误消息包含所有缺失字段
        self.assertIn("api_key", str(error))
        self.assertIn("base_url", str(error))
        self.assertIn("model_mappings", str(error))

        # 验证错误消息包含配置提示
        self.assertIn("请在设置中配置以下字段", str(error))
        self.assertIn("DashScope 视频生成服务", str(error))

        # 打印错误消息供人工查看
        print("\n" + "="*60)
        print("配置缺失错误示例：")
        print("="*60)
        print(str(error))
        print("="*60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
