"""测试全局任务轮询服务。"""

import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QCoreApplication

from config.manager import ConfigManager
from models.data_models import MessageStatus, ProviderConfig, TaskResult, TaskStatus
from providers.base import VideoProvider
from service.task_polling_service import TaskPollingService
from storage.database import DatabaseManager


class MockProvider(VideoProvider):
    """模拟 Provider 用于测试。"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.check_count = 0
        self.status_sequence = [TaskStatus.RUNNING, TaskStatus.RUNNING, TaskStatus.SUCCEEDED]
        self.video_url = "https://example.com/video.mp4"

    def submit(self, prompt: str, params: dict | None = None) -> str:
        return "mock_task_123"

    def check_status(self, task_id: str) -> TaskResult:
        self.check_count += 1
        status = self.status_sequence[min(self.check_count - 1, len(self.status_sequence) - 1)]
        return TaskResult(
            status=status,
            video_url=self.video_url if status == TaskStatus.SUCCEEDED else "",
        )

    def download(self, video_url: str, save_path: str, progress_callback=None) -> None:
        # 模拟下载，创建空文件
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(b"mock video data")
        if progress_callback:
            progress_callback(100, 100)

    def get_model_info(self) -> dict:
        return {"model": "mock-model", "capabilities": []}


class TestPollingService(unittest.TestCase):
    """测试轮询服务的核心功能。"""

    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.download_dir = os.path.join(self.temp_dir, "downloads")
        self.temp_files = os.path.join(self.temp_dir, "temp")

        # 初始化数据库和配置
        self.db = DatabaseManager(self.db_path)
        self.config = ConfigManager(self.config_path)
        self.config.upsert_provider(
            ProviderConfig(
                provider_name="mock",
                api_key="test_key",
                base_url="https://mock.api",
                default_model="mock-model",
            )
        )

        # 创建 QCoreApplication（测试信号槽需要）
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])

        # 创建轮询服务
        self.provider_registry = {"mock": MockProvider}
        self.polling_service = TaskPollingService(
            db=self.db,
            config=self.config,
            download_dir=self.download_dir,
            temp_dir=self.temp_files,
            provider_registry=self.provider_registry,
        )
        # 设置快速轮询以加速测试
        self.polling_service.poll_interval = 0.5
        self.polling_service.initial_delay = 0.1
        self.polling_service.idle_check_interval = 1.0

    def tearDown(self):
        self.polling_service.shutdown()
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_polling_service_starts_and_stops(self):
        """测试轮询服务的启动和停止。"""
        self.polling_service.start()
        time.sleep(0.2)
        self.assertIsNotNone(self.polling_service._worker)
        self.assertTrue(self.polling_service._worker.isRunning())

        self.polling_service.shutdown()
        self.assertIsNone(self.polling_service._worker)

    def test_idle_mode_when_no_tasks(self):
        """测试表空时进入空闲模式。"""
        self.polling_service.start()
        time.sleep(0.2)

        # 表空，worker 应该在运行但不做轮询
        tasks = self.db.list_active_tasks()
        self.assertEqual(len(tasks), 0)
        self.assertTrue(self.polling_service._worker.isRunning())

        self.polling_service.shutdown()

    def test_task_polling_workflow(self):
        """测试完整的任务轮询工作流。"""
        # 添加测试消息和任务
        from models.data_models import Conversation, Message

        conv = Conversation(
            id="conv_123",
            title="测试对话",
            created_at=datetime.now(),
            model_name="mock-model",
            provider_name="mock",
        )
        self.db.create_conversation(conv)

        msg = Message(
            id="msg_123",
            conversation_id="conv_123",
            role="assistant",
            content="生成视频测试",
            created_at=datetime.now(),
            task_id="mock_task_123",
            status=MessageStatus.GENERATING,
        )
        self.db.add_message(msg)
        self.db.add_active_task("mock_task_123", "msg_123", "mock", "mock-model")

        # 启动轮询服务
        finished_called = []
        self.polling_service.task_finished.connect(lambda mid, path: finished_called.append((mid, path)))

        self.polling_service.start()

        # 等待轮询完成（初始延迟 + 3 次轮询 + 下载）
        max_wait = 5.0
        elapsed = 0.0
        while elapsed < max_wait and len(finished_called) == 0:
            QCoreApplication.processEvents()
            time.sleep(0.1)
            elapsed += 0.1

        # 验证任务完成
        self.assertEqual(len(finished_called), 1)
        message_id, local_path = finished_called[0]
        self.assertEqual(message_id, "msg_123")
        self.assertTrue(os.path.exists(local_path))

        # 验证数据库状态
        updated_msg = self.db.get_message("msg_123")
        self.assertEqual(updated_msg.status, MessageStatus.COMPLETED)
        self.assertTrue(updated_msg.local_path)

        # 验证任务已从 active_tasks 移除
        active_tasks = self.db.list_active_tasks()
        self.assertEqual(len(active_tasks), 0)

        self.polling_service.shutdown()


if __name__ == "__main__":
    unittest.main()
