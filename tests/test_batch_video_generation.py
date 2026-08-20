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
        use_prev_shot_last_frame: bool = False,
        prev_shot_frame_service: MagicMock | None = None,
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
            use_prev_shot_last_frame=use_prev_shot_last_frame,
            cross_scene_prev_frame=False,
            prev_shot_frame_service=prev_shot_frame_service,
        )

    def test_prompt_extend_false_passed_to_submit_shot_video(self):
        video_service = MagicMock()
        video_service.start_shot_video.return_value = "task-1"

        controller = self._make_controller(prompt_extend=False, video_service=video_service)
        controller.run()

        request = video_service.start_shot_video.call_args.args[0]
        self.assertFalse(request.params["prompt_extend"])

    def test_prompt_extend_true_passed_to_submit_shot_video(self):
        video_service = MagicMock()
        video_service.start_shot_video.return_value = "task-1"

        controller = self._make_controller(prompt_extend=True, video_service=video_service)
        controller.run()

        request = video_service.start_shot_video.call_args.args[0]
        self.assertTrue(request.params["prompt_extend"])

    def test_negative_prompt_passed_when_non_empty(self):
        video_service = MagicMock()
        video_service.start_shot_video.return_value = "task-1"

        controller = self._make_controller(
            prompt_extend=True,
            video_service=video_service,
            negative_prompt="低质量\n模糊",
        )
        controller.run()

        request = video_service.start_shot_video.call_args.args[0]
        self.assertEqual(request.params["negative_prompt"], "低质量 模糊")

    def test_negative_prompt_omitted_when_empty(self):
        video_service = MagicMock()
        video_service.start_shot_video.return_value = "task-1"

        controller = self._make_controller(
            prompt_extend=True,
            video_service=video_service,
            negative_prompt="   ",
        )
        controller.run()

        request = video_service.start_shot_video.call_args.args[0]
        self.assertNotIn("negative_prompt", request.params)

    def test_batch_generate_videos_slot_accepts_prompt_extend(self):
        import inspect
        from bridge.storyboard_bridge import StoryboardBridge

        sig = inspect.signature(StoryboardBridge.batch_generate_videos)
        self.assertIn("prompt_extend", sig.parameters)
        self.assertIn("use_storyboard_design", sig.parameters)
        self.assertIn("use_character_design", sig.parameters)
        self.assertIn("negative_prompt", sig.parameters)
        self.assertIn("use_prev_shot_last_frame", sig.parameters)
        self.assertIn("cross_scene_prev_frame", sig.parameters)
        self.assertTrue(sig.parameters["prompt_extend"].default)
        self.assertTrue(sig.parameters["use_prev_shot_last_frame"].default)
        self.assertFalse(sig.parameters["cross_scene_prev_frame"].default)
        self.assertEqual(sig.parameters["negative_prompt"].default, "")

    def test_serial_mode_passes_prev_last_frame_to_submit(self):
        video_service = MagicMock()
        video_service.start_shot_video.return_value = "task-1"

        prev_service = MagicMock()
        prev_service.should_use_prev_frame.return_value = False

        controller = self._make_controller(
            prompt_extend=True,
            video_service=video_service,
            use_prev_shot_last_frame=True,
            prev_shot_frame_service=prev_service,
        )
        controller._wait_for_task = MagicMock(return_value=True)
        controller.run()

        video_service.start_shot_video.assert_called_once()
        request = video_service.start_shot_video.call_args.args[0]
        self.assertEqual(request.prev_shot_last_frame, "")
        controller._wait_for_task.assert_called_once_with("task-1")


if __name__ == "__main__":
    unittest.main()
