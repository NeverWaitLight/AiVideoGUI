import unittest

from models.api_params import (
    DashScopeVideoRequest,
    MediaItem,
    SeedanceVideoRequest,
)


class TestDashScopeVideoRequest(unittest.TestCase):

    def test_t2v_basic(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test prompt",
            resolution="1080P",
            ratio="16:9",
        )
        payload = request.to_dict()

        self.assertEqual(payload["model"], "wan2.7-t2v")
        self.assertEqual(payload["input"]["prompt"], "test prompt")
        self.assertEqual(payload["parameters"]["resolution"], "1080P")
        self.assertEqual(payload["parameters"]["ratio"], "16:9")

    def test_t2v_with_negative_prompt(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test",
            negative_prompt="low quality",
            resolution="720P",
        )
        payload = request.to_dict()

        self.assertEqual(payload["input"]["negative_prompt"], "low quality")
        self.assertEqual(payload["parameters"]["resolution"], "720P")

    def test_t2v_with_audio(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test",
            audio_url="https://example.com/audio.mp3",
        )
        payload = request.to_dict()

        self.assertEqual(payload["input"]["audio_url"], "https://example.com/audio.mp3")

    def test_t2v_with_extra_params(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test",
            resolution="720P",
            duration=10,
            watermark=True,
        )
        payload = request.to_dict()

        self.assertEqual(payload["parameters"]["duration"], 10)
        self.assertEqual(payload["parameters"]["watermark"], True)

    def test_r2v_with_media(self):
        media = [
            MediaItem(type="first_frame", url="https://example.com/frame.jpg"),
            MediaItem(
                type="reference_video",
                url="https://example.com/ref.mp4",
                reference_voice="https://example.com/voice.mp3",
            ),
            MediaItem(type="reference_image", url="https://example.com/ref.jpg"),
        ]

        request = DashScopeVideoRequest.for_r2v(
            model="wan2.7-r2v-2026-06-12",
            prompt="test",
            media=media,
            resolution="720P",
        )

        payload = request.to_dict()

        self.assertEqual(payload["model"], "wan2.7-r2v-2026-06-12")
        self.assertEqual(len(payload["input"]["media"]), 3)
        self.assertEqual(payload["input"]["media"][0]["type"], "first_frame")
        self.assertEqual(payload["input"]["media"][1]["type"], "reference_video")
        self.assertEqual(payload["input"]["media"][1]["reference_voice"], "https://example.com/voice.mp3")
        self.assertEqual(payload["input"]["media"][2]["type"], "reference_image")
        self.assertNotIn("reference_voice", payload["input"]["media"][2])

    def test_none_values_removed_in_input(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test",
            negative_prompt=None,
            audio_url=None,
            resolution="720P",
        )
        payload = request.to_dict()

        self.assertNotIn("negative_prompt", payload["input"])
        self.assertNotIn("audio_url", payload["input"])
        self.assertIn("resolution", payload["parameters"])

    def test_none_values_removed_in_parameters(self):
        request = DashScopeVideoRequest.for_t2v(
            model="wan2.7-t2v",
            prompt="test",
            resolution=None,
            ratio=None,
        )
        payload = request.to_dict()

        self.assertNotIn("resolution", payload["parameters"])
        self.assertNotIn("ratio", payload["parameters"])


class TestMediaItem(unittest.TestCase):

    def test_media_item_without_voice(self):
        item = MediaItem(type="reference_image", url="https://example.com/image.jpg")
        data = item.to_dict()

        self.assertEqual(data["type"], "reference_image")
        self.assertEqual(data["url"], "https://example.com/image.jpg")
        self.assertNotIn("reference_voice", data)

    def test_media_item_with_voice(self):
        item = MediaItem(
            type="reference_video",
            url="https://example.com/video.mp4",
            reference_voice="https://example.com/voice.mp3",
        )
        data = item.to_dict()

        self.assertEqual(data["type"], "reference_video")
        self.assertEqual(data["url"], "https://example.com/video.mp4")
        self.assertEqual(data["reference_voice"], "https://example.com/voice.mp3")


class TestSeedanceVideoRequest(unittest.TestCase):

    def test_t2v_basic(self):
        request = SeedanceVideoRequest.for_t2v(
            model="seedance-2.5",
            prompt="test",
            duration=10,
            quality="1080p",
            aspect_ratio="16:9",
        )
        payload = request.to_dict()

        self.assertEqual(payload["model"], "seedance-2.5")
        self.assertEqual(payload["prompt"], "test")
        self.assertEqual(payload["duration"], 10)
        self.assertEqual(payload["quality"], "1080p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertEqual(payload["generate_audio"], True)

    def test_t2v_with_web_search(self):
        request = SeedanceVideoRequest.for_t2v(
            model="seedance-2.5",
            prompt="test",
            web_search=True,
        )
        payload = request.to_dict()

        self.assertIn("model_params", payload)
        self.assertEqual(payload["model_params"]["web_search"], True)

    def test_t2v_without_web_search(self):
        request = SeedanceVideoRequest.for_t2v(
            model="seedance-2.5",
            prompt="test",
            web_search=None,
        )
        payload = request.to_dict()

        self.assertNotIn("model_params", payload)

    def test_t2v_with_callback_url(self):
        request = SeedanceVideoRequest.for_t2v(
            model="seedance-2.5",
            prompt="test",
            callback_url="https://example.com/callback",
        )
        payload = request.to_dict()

        self.assertEqual(payload["callback_url"], "https://example.com/callback")

    def test_t2v_defaults(self):
        request = SeedanceVideoRequest.for_t2v(
            model="seedance-2.0",
            prompt="test",
        )
        payload = request.to_dict()

        self.assertEqual(payload["duration"], 5)
        self.assertEqual(payload["quality"], "720p")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertEqual(payload["generate_audio"], True)


if __name__ == "__main__":
    unittest.main()
