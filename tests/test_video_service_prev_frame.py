import json
import unittest
from unittest.mock import MagicMock, patch

from service.video_service import VideoService


class TestVideoServicePrevFrame(unittest.TestCase):

    def setUp(self):
        self.session_manager = MagicMock()
        self.config = MagicMock()
        self.chat_service = MagicMock()
        self.service = VideoService(
            session_manager=self.session_manager,
            config=self.config,
            chat_service=self.chat_service,
            prompt_builder=MagicMock(),
            storyboard_service=MagicMock(),
            screenplay_service=MagicMock(),
            workspace_root="/tmp/workspace",
        )

    def _mock_provider(self):
        provider = MagicMock()
        provider._config.default_model = "test-model"
        provider.t2v.return_value = ("task-t2v", {"json": {}})
        provider.p2v.return_value = ("task-p2v", {"json": {}})
        provider.r2v.return_value = ("task-r2v", {"json": {}})
        self.service.get_provider = MagicMock(return_value=provider)
        return provider

    def _mock_repos(self):
        task_repo = MagicMock()
        task_repo.add.return_value = 1
        take_repo = MagicMock()
        take_repo.get_next_number.return_value = 1

        def get_repo(repo_class):
            name = getattr(repo_class, "__name__", str(repo_class))
            if "GenerateTask" in name:
                return task_repo
            return take_repo

        self.session_manager.get_repo.side_effect = get_repo
        return task_repo, take_repo

    @patch("service.video_service.paths.workspace_root", return_value="/workspace")
    @patch("service.video_service.to_relative_path", return_value="projects/1/1-1-1.mp4")
    def test_submit_task_uses_p2v_when_only_prev_last_frame(self, *_mocks):
        provider = self._mock_provider()
        self._mock_repos()

        self.service.submit_task(
            prompt="test prompt",
            provider_name="dashscope",
            prev_shot_last_frame="/frames/prev_last.jpg",
            project_id=1,
            storyboard_id=10,
            scene_number=1,
            shot_number=1,
        )

        provider.p2v.assert_called_once()
        provider.r2v.assert_not_called()
        provider.t2v.assert_not_called()
        self.assertEqual(provider.p2v.call_args.kwargs["image_path"], "/frames/prev_last.jpg")

    @patch("service.video_service.paths.workspace_root", return_value="/workspace")
    @patch("service.video_service.to_relative_path", return_value="projects/1/1-1-1.mp4")
    def test_submit_task_uses_r2v_with_first_frame_when_prev_and_reference(self, *_mocks):
        provider = self._mock_provider()
        self._mock_repos()

        self.service.submit_task(
            prompt="test prompt",
            provider_name="dashscope",
            reference_images=["/design.jpg"],
            prev_shot_last_frame="/frames/prev_last.jpg",
            project_id=1,
            storyboard_id=10,
            scene_number=1,
            shot_number=1,
        )

        provider.r2v.assert_called_once()
        params = provider.r2v.call_args.kwargs["params"]
        self.assertEqual(params["first_frame_path"], "/frames/prev_last.jpg")
        provider.p2v.assert_not_called()

    @patch("service.video_service.paths.workspace_root", return_value="/workspace")
    @patch("service.video_service.to_relative_path", return_value="projects/1/1-1-1.mp4")
    def test_submit_task_uses_t2v_without_prev_or_reference(self, *_mocks):
        provider = self._mock_provider()
        self._mock_repos()

        self.service.submit_task(
            prompt="test prompt",
            provider_name="dashscope",
            project_id=1,
            storyboard_id=10,
            scene_number=1,
            shot_number=1,
        )

        provider.t2v.assert_called_once()
        provider.p2v.assert_not_called()
        provider.r2v.assert_not_called()


if __name__ == "__main__":
    unittest.main()
