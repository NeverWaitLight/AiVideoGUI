import unittest
from unittest.mock import MagicMock

from models.enums import GenerateTaskCallerType, GenerateTaskType
from providers.generate_task_recorder import GenerateTaskRecorder
from storage.repositories.generate_task_repository import GenerateTaskRepository


class TestGenerateTaskRecorder(unittest.TestCase):
    def setUp(self):
        self.task_repo = MagicMock()
        self.task_repo.add.return_value = 42
        self.session_manager = MagicMock()
        self.session_manager.get_repo.return_value = self.task_repo
        self.recorder = GenerateTaskRecorder(self.session_manager)

    def test_create_pending_commits_task(self):
        provider_task_id, task_id = self.recorder.create_pending(
            provider_name="dashscope",
            model_name="qwen-max",
            request_params={"messages": []},
            task_type=GenerateTaskType.CHAT,
            parent_ids="101",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id="42",
            project_id=1,
        )

        self.assertEqual(task_id, 42)
        self.assertTrue(provider_task_id)
        add_kwargs = self.task_repo.add.call_args.kwargs
        self.assertEqual(add_kwargs["type"], GenerateTaskType.CHAT)
        self.assertEqual(add_kwargs["parent_ids"], "101")
        self.session_manager.commit_write.assert_called()

    def test_get_parent_task_id_parses_first_id(self):
        self.assertEqual(GenerateTaskRepository.get_parent_task_id("101,202"), 101)
        self.assertIsNone(GenerateTaskRepository.get_parent_task_id(""))
        self.assertIsNone(GenerateTaskRepository.get_parent_task_id("invalid"))

    def test_mark_succeeded_stores_response_data(self):
        self.recorder.mark_succeeded(42, remote_url="https://example.com/a.png", response_data='{"ok":true}')
        kwargs = self.task_repo.update_status.call_args.kwargs
        self.assertEqual(kwargs["remote_url"], "https://example.com/a.png")
        self.assertEqual(kwargs["response_data"], '{"ok":true}')
        self.task_repo.mark_completed.assert_called_once_with(42)
        self.session_manager.commit_write.assert_called()


if __name__ == "__main__":
    unittest.main()
