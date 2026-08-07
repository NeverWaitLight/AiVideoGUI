import os
import tempfile
import unittest

from di import ApplicationContainer


class TestDependencyInjection(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.temp_dir, "workspace")
        self.config_path = os.path.join(self.temp_dir, "settings.json")

        os.makedirs(self.workspace_root, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write('{"providers": [], "app_settings": {}}')

        self.container = ApplicationContainer()
        self.container.config.workspace_root.from_value(self.workspace_root)
        self.container.config.config_path.from_value(self.config_path)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        self.container.reset_singletons()

    def test_singleton_pattern(self):
        service1 = self.container.video_service()
        service2 = self.container.video_service()
        self.assertIs(service1, service2, "VideoService 应该是单例")

    def test_dependency_injection(self):
        video_service = self.container.video_service()

        self.assertIsNotNone(video_service._sm, "SessionManager 应该被注入")
        self.assertIsNotNone(video_service._config, "ConfigManager 应该被注入")

    def test_config_propagation(self):
        config_manager = self.container.config_manager()

        self.assertEqual(config_manager._path, self.config_path, "ConfigManager 应该使用正确的配置路径")

    def test_all_services_instantiation(self):
        services = [
            self.container.video_service,
            self.container.media_service,
            self.container.project_service,
            self.container.story_outline_service,
            self.container.screenplay_service,
            self.container.storyboard_service,
            self.container.character_service,
            self.container.chat_model_service,
            self.container.image_service,
            self.container.visual_style_service,
        ]

        for service_provider in services:
            with self.subTest(service=service_provider):
                service = service_provider()
                self.assertIsNotNone(service, f"{service_provider} 应该能够实例化")

    def test_shared_session_manager(self):
        video_service = self.container.video_service()
        media_service = self.container.media_service()

        self.assertIs(video_service._sm, media_service._sm,
                     "所有 Service 应该共享同一个 SessionManager 实例")


if __name__ == "__main__":
    unittest.main()
