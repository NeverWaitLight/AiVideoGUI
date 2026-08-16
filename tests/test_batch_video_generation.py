import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import QObject, QCoreApplication, Signal

from bridge.workers import BatchGenerationController
from models.enums import ShotSize
from models.storyboard import Storyboard


def _make_storyboard(**kwargs) -> Storyboard:
    defaults = {
        "id": 1,
        "scene_id": 101,
        "scene_number": 1,
        "shot_number": 1,
        "shot_size": ShotSize.MEDIUM_SHOT,
        "camera_movement": "固定",
        "content": "主角站在窗前",
        "sound_effect": "",
        "ambient_sound": "",
        "background_music": "",
        "duration": 5.0,
        "notes": "",
        "design_image": "",
        "created_at": 1000000,
        "updated_at": 1000000,
    }
    defaults.update(kwargs)
    return Storyboard(**defaults)


class _SignalEmitter(QObject):
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)


class TestBatchVideoGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QCoreApplication.instance() or QCoreApplication([])

    def _make_controller(
        self,
        prompt_extend: bool,
        video_service: MagicMock,
        negative_prompt: str = "",
    ) -> BatchGenerationController:
        project = MagicMock()
        project.id = 1
        project.name = "测试项目"
        project.resolution = "720P"
        project.aspect_ratio = "16:9"

        provider_cfg = MagicMock()
        provider_cfg.default_params = {"watermark": False, "prompt_extend": True}

        shot_list = [{
            "scene_number": 1,
            "shot_number": 1,
            "storyboard": _make_storyboard(),
            "scene": None,
            "prev_shot": None,
            "next_shot": None,
            "reference_images": [],
            "reference_images_info": [],
            "visual_style": None,
        }]

        return BatchGenerationController(
            shot_list=shot_list,
            video_service=video_service,
            signal_emitter=_SignalEmitter(),
            provider_name="dashscope",
            project=project,
            provider_cfg=provider_cfg,
            prompt_extend=prompt_extend,
            negative_prompt=negative_prompt,
        )

    def test_prompt_extend_false_passed_to_submit_shot_video(self):
        video_service = MagicMock()
        video_service.submit_shot_video.return_value = "task-1"

        controller = self._make_controller(prompt_extend=False, video_service=video_service)
        controller.run()

        params = video_service.submit_shot_video.call_args.kwargs["params"]
        self.assertFalse(params["prompt_extend"])

    def test_prompt_extend_true_passed_to_submit_shot_video(self):
        video_service = MagicMock()
        video_service.submit_shot_video.return_value = "task-1"

        controller = self._make_controller(prompt_extend=True, video_service=video_service)
        controller.run()

        params = video_service.submit_shot_video.call_args.kwargs["params"]
        self.assertTrue(params["prompt_extend"])

    def test_negative_prompt_passed_when_non_empty(self):
        video_service = MagicMock()
        video_service.submit_shot_video.return_value = "task-1"

        controller = self._make_controller(
            prompt_extend=True,
            video_service=video_service,
            negative_prompt="低质量\n模糊",
        )
        controller.run()

        params = video_service.submit_shot_video.call_args.kwargs["params"]
        self.assertEqual(params["negative_prompt"], "低质量 模糊")

    def test_negative_prompt_omitted_when_empty(self):
        video_service = MagicMock()
        video_service.submit_shot_video.return_value = "task-1"

        controller = self._make_controller(
            prompt_extend=True,
            video_service=video_service,
            negative_prompt="   ",
        )
        controller.run()

        params = video_service.submit_shot_video.call_args.kwargs["params"]
        self.assertNotIn("negative_prompt", params)

    def test_batch_generate_videos_slot_accepts_prompt_extend(self):
        import inspect
        from bridge.storyboard_bridge import StoryboardBridge

        sig = inspect.signature(StoryboardBridge.batch_generate_videos)
        self.assertIn("prompt_extend", sig.parameters)
        self.assertIn("use_storyboard_design", sig.parameters)
        self.assertIn("use_character_design", sig.parameters)
        self.assertIn("negative_prompt", sig.parameters)
        self.assertTrue(sig.parameters["prompt_extend"].default)
        self.assertEqual(sig.parameters["negative_prompt"].default, "")


if __name__ == "__main__":
    unittest.main()
