"""测试 active_tasks 表的 save_path 字段和分镜序号计算。"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from models.data_models import (
    Conversation,
    MediaFile,
    MediaType,
    Message,
    MessageStatus,
)
from storage.database import DatabaseManager


class TestActiveTaskSavePath(unittest.TestCase):
    """测试 active_tasks 表 save_path 字段。"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_conversation_and_message(self):
        conv = Conversation(
            id="conv_1",
            title="测试对话",
            created_at=datetime.now(),
        )
        self.db.create_conversation(conv)

        msg = Message(
            id="msg_1",
            conversation_id="conv_1",
            role="assistant",
            content="test",
            created_at=datetime.now(),
            task_id="task_1",
            status=MessageStatus.GENERATING,
        )
        self.db.add_message(msg)

    def test_add_active_task_with_save_path(self):
        """add_active_task 应正确保存 save_path（相对路径）。"""
        self._setup_conversation_and_message()
        self.db.add_active_task(
            task_id="task_1",
            message_id="msg_1",
            provider_name="dashscope",
            model_name="wan2.7-t2v",
            save_path="1-3-2.mp4",
        )

        tasks = self.db.list_active_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["save_path"], "1-3-2.mp4")

    def test_add_active_task_without_save_path(self):
        """不传 save_path 时应默认为空字符串。"""
        self._setup_conversation_and_message()
        self.db.add_active_task(
            task_id="task_1",
            message_id="msg_1",
            provider_name="dashscope",
            model_name="wan2.7-t2v",
        )

        tasks = self.db.list_active_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["save_path"], "")

    def test_get_next_storyboard_seq_empty(self):
        """无已有素材时序号应为 1。"""
        seq = self.db.get_next_storyboard_seq(1, 1)
        self.assertEqual(seq, 1)

    def test_get_next_storyboard_seq_with_media(self):
        """有已完成素材时序号应递增。"""
        for i in range(1, 4):
            media = MediaFile(
                id=f"media_{i}",
                filename=f"1-2-{i}.mp4",
                media_type=MediaType.VIDEO,
                local_path=f"/videos/1-2-{i}.mp4",
            )
            self.db.add_media_file(media)

        seq = self.db.get_next_storyboard_seq(1, 2)
        self.assertEqual(seq, 4)

    def test_get_next_storyboard_seq_with_pending_tasks(self):
        """有待处理任务时序号应跳过已占用的值。"""
        # 已完成的素材 1-1-1.mp4
        media = MediaFile(
            id="media_1",
            filename="1-1-1.mp4",
            media_type=MediaType.VIDEO,
            local_path="/videos/1-1-1.mp4",
        )
        self.db.add_media_file(media)

        # 待处理任务 save_path 指向 1-1-2.mp4（相对路径）
        self._setup_conversation_and_message()
        self.db.add_active_task(
            task_id="task_1",
            message_id="msg_1",
            provider_name="dashscope",
            model_name="wan2.7-t2v",
            save_path="1-1-2.mp4",
        )

        seq = self.db.get_next_storyboard_seq(1, 1)
        self.assertEqual(seq, 3)

    def test_get_next_storyboard_seq_different_shots(self):
        """不同场次-镜头的序号应独立计算。"""
        media = MediaFile(
            id="media_1",
            filename="2-3-1.mp4",
            media_type=MediaType.VIDEO,
            local_path="/videos/2-3-1.mp4",
        )
        self.db.add_media_file(media)

        seq_2_3 = self.db.get_next_storyboard_seq(2, 3)
        seq_1_1 = self.db.get_next_storyboard_seq(1, 1)
        self.assertEqual(seq_2_3, 2)
        self.assertEqual(seq_1_1, 1)


if __name__ == "__main__":
    unittest.main()
