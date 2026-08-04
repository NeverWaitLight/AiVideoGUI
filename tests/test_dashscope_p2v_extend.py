import unittest
from unittest.mock import MagicMock, patch

from models.provider_config import ProviderConfig
from providers.dashscope_video import DashScopeVideoProvider


class TestDashScopeP2VExtend(unittest.TestCase):

    def setUp(self):
        config = ProviderConfig(
            provider_name="dashscope",
            api_key="test-api-key",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            default_model="wan2.7-i2v-2026-04-25",
        )
        self.provider = DashScopeVideoProvider(config)

    @patch("providers.dashscope_video.requests.post")
    def test_p2v_first_frame_only(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-123"},
            "request_id": "req-123",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.p2v(
            prompt="一只小猫在草地上奔跑",
            image_path="https://example.com/first_frame.jpg",
            params={"resolution": "720P", "duration": 10},
        )

        self.assertEqual(task_id, "test-task-123")
        self.assertIn("url", request_details)
        self.assertIn("json", request_details)
        self.assertIn("headers", request_details)

        payload = request_details["json"]
        self.assertEqual(payload["model"], "wan2.7-i2v-2026-04-25")
        self.assertEqual(payload["input"]["prompt"], "一只小猫在草地上奔跑")
        self.assertEqual(len(payload["input"]["media"]), 1)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_frame")
        self.assertEqual(payload["input"]["media"][0]["url"], "https://example.com/first_frame.jpg")
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(payload["parameters"]["duration"], 10)

    @patch("providers.dashscope_video.requests.post")
    def test_p2v_first_and_last_frame(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-456"},
            "request_id": "req-456",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.p2v(
            prompt="一只小猫从坐姿变为站立",
            image_path="https://example.com/first_frame.jpg",
            params={
                "resolution": "720P",
                "duration": 10,
                "last_frame_path": "https://example.com/last_frame.jpg",
            },
        )

        self.assertEqual(task_id, "test-task-456")

        payload = request_details["json"]
        self.assertEqual(len(payload["input"]["media"]), 2)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_frame")
        self.assertEqual(payload["input"]["media"][0]["url"], "https://example.com/first_frame.jpg")
        self.assertEqual(payload["input"]["media"][1]["type"], "last_frame")
        self.assertEqual(payload["input"]["media"][1]["url"], "https://example.com/last_frame.jpg")

        self.assertNotIn("last_frame_path", payload["parameters"])

    @patch("providers.dashscope_video.requests.post")
    def test_p2v_with_driving_audio(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-789"},
            "request_id": "req-789",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.p2v(
            prompt="一个说唱歌手在表演",
            image_path="https://example.com/first_frame.jpg",
            params={
                "resolution": "720P",
                "duration": 10,
                "driving_audio_path": "https://example.com/rap.mp3",
            },
        )

        self.assertEqual(task_id, "test-task-789")

        payload = request_details["json"]
        self.assertEqual(len(payload["input"]["media"]), 2)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_frame")
        self.assertEqual(payload["input"]["media"][1]["type"], "driving_audio")
        self.assertEqual(payload["input"]["media"][1]["url"], "https://example.com/rap.mp3")

        self.assertNotIn("driving_audio_path", payload["parameters"])

    @patch("providers.dashscope_video.requests.post")
    def test_extend_video_only(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-ext-123"},
            "request_id": "req-ext-123",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.extend(
            prompt="女孩背着书包出门",
            video_path="https://example.com/first_clip.mp4",
            params={"resolution": "720P", "duration": 15},
        )

        self.assertEqual(task_id, "test-task-ext-123")

        payload = request_details["json"]
        self.assertEqual(payload["model"], "wan2.7-i2v-2026-04-25")
        self.assertEqual(payload["input"]["prompt"], "女孩背着书包出门")
        self.assertEqual(len(payload["input"]["media"]), 1)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_clip")
        self.assertEqual(payload["input"]["media"][0]["url"], "https://example.com/first_clip.mp4")
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(payload["parameters"]["duration"], 15)

    @patch("providers.dashscope_video.requests.post")
    def test_extend_video_with_last_frame(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-ext-456"},
            "request_id": "req-ext-456",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.extend(
            prompt="女孩走到门外",
            video_path="https://example.com/first_clip.mp4",
            params={
                "resolution": "720P",
                "duration": 15,
                "last_frame_path": "https://example.com/last_frame.jpg",
            },
        )

        self.assertEqual(task_id, "test-task-ext-456")

        payload = request_details["json"]
        self.assertEqual(len(payload["input"]["media"]), 2)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_clip")
        self.assertEqual(payload["input"]["media"][0]["url"], "https://example.com/first_clip.mp4")
        self.assertEqual(payload["input"]["media"][1]["type"], "last_frame")
        self.assertEqual(payload["input"]["media"][1]["url"], "https://example.com/last_frame.jpg")

        self.assertNotIn("last_frame_path", payload["parameters"])

    @patch("providers.dashscope_video.requests.post")
    def test_p2v_all_media_types(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-all"},
            "request_id": "req-all",
        }
        mock_post.return_value = mock_response

        task_id, request_details = self.provider.p2v(
            prompt="完整的视频场景",
            image_path="https://example.com/first_frame.jpg",
            params={
                "resolution": "1080P",
                "duration": 10,
                "last_frame_path": "https://example.com/last_frame.jpg",
                "driving_audio_path": "https://example.com/audio.mp3",
            },
        )

        self.assertEqual(task_id, "test-task-all")

        payload = request_details["json"]
        self.assertEqual(len(payload["input"]["media"]), 3)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_frame")
        self.assertEqual(payload["input"]["media"][1]["type"], "last_frame")
        self.assertEqual(payload["input"]["media"][2]["type"], "driving_audio")

        self.assertNotIn("last_frame_path", payload["parameters"])
        self.assertNotIn("driving_audio_path", payload["parameters"])


if __name__ == "__main__":
    unittest.main()
