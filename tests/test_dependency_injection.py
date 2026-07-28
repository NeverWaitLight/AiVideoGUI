"""测试依赖注入容器。"""

import os
import tempfile
import unittest

from di import ApplicationContainer


class TestDependencyInjection(unittest.TestCase):
    """测试 ApplicationContainer 的依赖注入功能。"""

    def setUp(self):
        """创建临时工作区和配置文件。"""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.temp_dir, "workspace")
        self.config_path = os.path.join(self.temp_dir, "config.json")

        # 创建工作区目录
        os.makedirs(self.workspace_root, exist_ok=True)

        # 创建空配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write('{"providers": [], "app_settings": {}}')

        # 创建容器并配置
        self.container = ApplicationContainer()
        self.container.config.workspace_root.from_value(self.workspace_root)
        self.container.config.config_path.from_value(self.config_path)

    def tearDown(self):
        """清理临时文件。"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # 重置容器单例
        self.container.reset_singletons()

    def test_singleton_pattern(self):
        """测试单例模式：多次调用返回同一实例。"""
        service1 = self.container.video_service()
        service2 = self.container.video_service()
        self.assertIs(service1, service2, "VideoService 应该是单例")

    def test_dependency_injection(self):
        """测试依赖注入：Service 自动注入 SessionManager 和 ConfigManager。"""
        video_service = self.container.video_service()

        # 验证 VideoService 的依赖已正确注入
        self.assertIsNotNone(video_service._sm, "SessionManager 应该被注入")
        self.assertIsNotNone(video_service._config, "ConfigManager 应该被注入")

    def test_config_propagation(self):
        """测试配置传播：容器配置正确传递给 Service。"""
        config_manager = self.container.config_manager()

        # 验证 ConfigManager 接收到正确的配置路径
        self.assertEqual(config_manager._path, self.config_path, "ConfigManager 应该使用正确的配置路径")

    def test_all_services_instantiation(self):
        """测试所有 Service 都能正常实例化。"""
        services = [
            self.container.video_service,
            self.container.media_service,
            self.container.project_service,
            self.container.story_outline_service,
            self.container.screenplay_service,
            self.container.storyboard_service,
            self.container.character_service,
            self.container.chat_service,
            self.container.text_model_service,
            self.container.image_service,
            self.container.task_polling_service,
        ]

        for service_provider in services:
            with self.subTest(service=service_provider):
                service = service_provider()
                self.assertIsNotNone(service, f"{service_provider} 应该能够实例化")

    def test_shared_session_manager(self):
        """测试所有 Service 共享同一个 SessionManager 实例。"""
        video_service = self.container.video_service()
        media_service = self.container.media_service()

        # 验证两个 Service 使用同一个 SessionManager
        self.assertIs(video_service._sm, media_service._sm,
                     "所有 Service 应该共享同一个 SessionManager 实例")


if __name__ == "__main__":
    unittest.main()
