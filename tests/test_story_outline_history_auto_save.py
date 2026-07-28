"""测试 StoryOutline 历史版本自动保存功能。"""

import os
import tempfile
import time
import unittest
from datetime import datetime

from models.project import Project
from models.story_outline import StoryOutline
from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.project import ProjectRepository
from storage.repositories.story_outline import StoryOutlineRepository, StoryOutlineHistoryRepository


class TestStoryOutlineHistoryAutoSave(unittest.TestCase):
    """测试 StoryOutline 创建/更新时自动保存历史版本。"""

    def setUp(self):
        """创建临时数据库。"""
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        database_url = f"sqlite:///{self.temp_db_path}"
        init_engine(database_url, echo=False)
        create_all_tables()

    def tearDown(self):
        """删除临时数据库。"""
        from storage.orm.base import engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_outline(self, content="初始大纲内容"):
        """辅助方法：创建项目和大纲。"""
        session = get_session()
        project_repo = ProjectRepository(session)
        outline_repo = StoryOutlineRepository(session)

        now_ms = int(time.time() * 1000)
        project = Project(
            id=0,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
            created_at=now_ms,
            updated_at=now_ms,
            cover_image="",
        )
        project = project_repo.create(project)
        session.commit()

        story_outline = StoryOutline(
            id=0,
            project_id=project.id,
            content=content,
            created_at=now_ms,
            updated_at=now_ms,
        )
        story_outline = outline_repo.create(story_outline)
        session.commit()

        return project, story_outline

    def test_auto_save_history_on_insert(self):
        """测试创建大纲时自动保存初始快照。"""
        project, story_outline = self._create_project_and_outline("初始大纲内容")

        session = get_session()
        history_repo = StoryOutlineHistoryRepository(session)
        history_list = history_repo.list_by_story_outline(story_outline.id)

        self.assertEqual(len(history_list), 1, "创建大纲后应自动保存 1 条历史")
        self.assertEqual(history_list[0].content, "初始大纲内容")
        self.assertEqual(history_list[0].story_outline_id, story_outline.id)
        self.assertEqual(history_list[0].project_id, project.id)

    def test_auto_save_history_on_update(self):
        """测试更新 StoryOutline 时自动保存历史版本。"""
        project, story_outline = self._create_project_and_outline()

        session = get_session()
        outline_repo = StoryOutlineRepository(session)
        history_repo = StoryOutlineHistoryRepository(session)

        now_ms = int(time.time() * 1000)
        outline_repo.update_content(story_outline.id, "第一次修改的内容", now_ms)

        history_list = history_repo.list_by_story_outline(story_outline.id)
        self.assertEqual(len(history_list), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history_list[0].content, "第一次修改的内容")
        self.assertEqual(history_list[0].story_outline_id, story_outline.id)
        self.assertEqual(history_list[0].project_id, project.id)

        now_ms = int(time.time() * 1000)
        outline_repo.update_content(story_outline.id, "第二次修改的内容", now_ms)

        history_list = history_repo.list_by_story_outline(story_outline.id)
        self.assertEqual(len(history_list), 3, "创建+2次更新应有 3 条历史记录")
        self.assertEqual(history_list[0].content, "第二次修改的内容")
        self.assertEqual(history_list[1].content, "第一次修改的内容")

    def test_history_contains_project_id(self):
        """测试历史记录包含 project_id 字段。"""
        project, story_outline = self._create_project_and_outline("初始内容")

        session = get_session()
        outline_repo = StoryOutlineRepository(session)
        history_repo = StoryOutlineHistoryRepository(session)

        now_ms = int(time.time() * 1000)
        outline_repo.update_content(story_outline.id, "新内容", now_ms)

        history_list = history_repo.list_by_story_outline(story_outline.id)
        self.assertEqual(len(history_list), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history_list[0].project_id, project.id, "历史记录应包含 project_id")


if __name__ == "__main__":
    unittest.main()
