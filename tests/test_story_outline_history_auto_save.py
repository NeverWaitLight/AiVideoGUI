"""测试 StoryOutline 历史版本自动保存功能。"""

import os
import tempfile
import time
import unittest
from datetime import datetime

from models.data_models import StoryOutline, Project
from storage.database import DatabaseManager


class TestStoryOutlineHistoryAutoSave(unittest.TestCase):
    """测试 StoryOutline 创建/更新时自动保存历史版本。"""

    def setUp(self):
        """创建临时数据库。"""
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        self.db = DatabaseManager(self.temp_db_path)

    def tearDown(self):
        """删除临时数据库。"""
        from storage.orm.base import close_session, engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_outline(self, content="初始大纲内容"):
        """辅助方法：创建项目和大纲。"""
        project = self.db.create_project(
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
        )
        now_ms = int(time.time() * 1000)
        story_outline = self.db.create_story_outline(
            StoryOutline(
                id=0,
                project_id=project.id,
                content=content,
                created_at=now_ms,
                updated_at=now_ms,
            )
        )
        return project, story_outline

    def test_auto_save_history_on_insert(self):
        """测试创建大纲时自动保存初始快照。"""
        project, story_outline = self._create_project_and_outline("初始大纲内容")

        history_list = self.db.list_story_outline_history(story_outline.id)
        self.assertEqual(len(history_list), 1, "创建大纲后应自动保存 1 条历史")
        self.assertEqual(history_list[0].content, "初始大纲内容")
        self.assertEqual(history_list[0].story_outline_id, story_outline.id)
        self.assertEqual(history_list[0].project_id, project.id)

    def test_auto_save_history_on_update(self):
        """测试更新 StoryOutline 时自动保存历史版本。"""
        project, story_outline = self._create_project_and_outline()

        self.db.update_story_outline(story_outline.id, "第一次修改的内容")

        history_list = self.db.list_story_outline_history(story_outline.id)
        self.assertEqual(len(history_list), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history_list[0].content, "第一次修改的内容")
        self.assertEqual(history_list[0].story_outline_id, story_outline.id)
        self.assertEqual(history_list[0].project_id, project.id)

        self.db.update_story_outline(story_outline.id, "第二次修改的内容")

        history_list = self.db.list_story_outline_history(story_outline.id)
        self.assertEqual(len(history_list), 3, "创建+2次更新应有 3 条历史记录")
        self.assertEqual(history_list[0].content, "第二次修改的内容")
        self.assertEqual(history_list[1].content, "第一次修改的内容")

    def test_history_contains_project_id(self):
        """测试历史记录包含 project_id 字段。"""
        project, story_outline = self._create_project_and_outline("初始内容")

        self.db.update_story_outline(story_outline.id, "新内容")

        history_list = self.db.list_story_outline_history(story_outline.id)
        self.assertEqual(len(history_list), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history_list[0].project_id, project.id, "历史记录应包含 project_id")


if __name__ == "__main__":
    unittest.main()
