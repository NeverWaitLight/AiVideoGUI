import os
import tempfile
import time
import unittest
import uuid

from models.enums import GenerateTaskType
from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.generate_task_repository import GenerateTaskRepository

# 注册全部 ORM 实体以便 create_all_tables 正确建表
import storage.orm.character_entity  # noqa: F401
import storage.orm.media_entity  # noqa: F401
import storage.orm.oss_cache_entity  # noqa: F401
import storage.orm.project_entity  # noqa: F401
import storage.orm.screenplay_entity  # noqa: F401
import storage.orm.story_outline_entity  # noqa: F401
import storage.orm.storyboard_entity  # noqa: F401
import storage.orm.storyboard_take_entity  # noqa: F401
import storage.orm.visual_style_entity  # noqa: F401


class TestGenerateTaskRepository(unittest.TestCase):

    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        database_url = f"sqlite:///{self.temp_db_path}"
        init_engine(database_url, echo=False)
        create_all_tables()

        self.session = get_session()
        self.repo = GenerateTaskRepository(self.session)

    def tearDown(self):
        from storage.orm.base import engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _add_task(self, parent_ids: str = "", task_type: GenerateTaskType = GenerateTaskType.VIDEO) -> int:
        now = int(time.time() * 1000)
        return self.repo.add(
            provider_task_id=f"task-{uuid.uuid4()}",
            provider_name="dashscope",
            model_name="test-model",
            local_path="",
            request_params="{}",
            type=task_type,
            parent_ids=parent_ids,
        )

    def test_list_tasks_with_filters_excludes_child_tasks(self):
        parent_id = self._add_task(parent_ids="")
        self._add_task(parent_ids=str(parent_id), task_type=GenerateTaskType.CHAT)
        self._add_task(parent_ids=str(parent_id), task_type=GenerateTaskType.IMAGE)
        self.session.commit()

        tasks = self.repo.list_tasks_with_filters()
        task_ids = [t["id"] for t in tasks]

        self.assertIn(parent_id, task_ids)
        self.assertEqual(len(task_ids), 1)

    def test_list_child_tasks_by_parent_id_returns_sorted_children(self):
        parent_id = self._add_task(parent_ids="")
        child1 = self._add_task(parent_ids=str(parent_id), task_type=GenerateTaskType.CHAT)
        child2 = self._add_task(parent_ids=str(parent_id), task_type=GenerateTaskType.IMAGE)
        other_parent = self._add_task(parent_ids="")
        self._add_task(parent_ids=str(other_parent), task_type=GenerateTaskType.VIDEO)
        self.session.commit()

        children = self.repo.list_child_tasks_by_parent_id(parent_id)
        child_ids = [c["id"] for c in children]

        self.assertEqual(child_ids, sorted([child1, child2]))
        self.assertNotIn(other_parent, child_ids)

    def test_list_child_tasks_by_parent_id_supports_chained_parent_ids(self):
        root_id = self._add_task(parent_ids="")
        nested_id = self._add_task(parent_ids=str(root_id), task_type=GenerateTaskType.CHAT)
        deep_child = self._add_task(parent_ids=f"{root_id},{nested_id}", task_type=GenerateTaskType.IMAGE)
        self.session.commit()

        root_children = self.repo.list_child_tasks_by_parent_id(root_id)
        nested_children = self.repo.list_child_tasks_by_parent_id(nested_id)

        self.assertEqual([c["id"] for c in root_children], [nested_id])
        self.assertEqual([c["id"] for c in nested_children], [deep_child])

    def test_fail_incomplete_sync_wait_tasks_marks_chat_and_image_only(self):
        chat_id = self._add_task(task_type=GenerateTaskType.CHAT)
        image_id = self._add_task(task_type=GenerateTaskType.IMAGE)
        video_id = self._add_task(task_type=GenerateTaskType.VIDEO)
        done_image_id = self._add_task(task_type=GenerateTaskType.IMAGE)
        self.repo.update_status(done_image_id, "succeeded")
        self.repo.mark_completed(done_image_id)
        self.session.commit()

        n = self.repo.fail_incomplete_sync_wait_tasks("应用退出时任务未完成")
        self.session.commit()

        self.assertEqual(n, 2)

        chat = self.repo.get_by_id(chat_id)
        image = self.repo.get_by_id(image_id)
        video = self.repo.get_by_id(video_id)
        done_image = self.repo.get_by_id(done_image_id)

        self.assertEqual(chat["status"], "failed")
        self.assertTrue(chat["completed"])
        self.assertEqual(chat["error_message"], "应用退出时任务未完成")

        self.assertEqual(image["status"], "failed")
        self.assertTrue(image["completed"])
        self.assertEqual(image["error_message"], "应用退出时任务未完成")

        self.assertEqual(video["status"], "pending")
        self.assertFalse(video["completed"])

        self.assertEqual(done_image["status"], "succeeded")
        self.assertTrue(done_image["completed"])


if __name__ == "__main__":
    unittest.main()
