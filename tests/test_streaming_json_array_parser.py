import unittest

from utils.script_parser import ScriptParser
from utils.shot_parser import ShotParser
from utils.streaming_json_array_parser import StreamingJsonArrayParser


SAMPLE_SCRIPT_JSON = """{
  "title": "夜班",
  "scenes": [
    {
      "scene_number": 1,
      "location_type": "interior",
      "location": "医院走廊",
      "time_type": "night",
      "time_detail": "",
      "content": "深夜的住院部走廊空无一人。"
    },
    {
      "scene_number": 2,
      "location_type": "interior",
      "location": "旧病房门口",
      "time_type": "night",
      "time_detail": "",
      "content": "林晚走到病房门前，门虚掩着。"
    }
  ]
}"""

SAMPLE_STORYBOARD_JSON = """{
  "storyboard": [
    {
      "scene_number": 1,
      "shot_number": 1,
      "shot_size": "medium_shot",
      "camera_movement": "固定",
      "content": "走廊全景",
      "duration": 3.0
    },
    {
      "scene_number": 1,
      "shot_number": 2,
      "shot_size": "close_up",
      "camera_movement": "推",
      "content": "林晚面部特写",
      "duration": 2.5
    }
  ]
}"""


class TestStreamingJsonArrayParser(unittest.TestCase):
    def _feed_in_chunks(self, parser: StreamingJsonArrayParser, text: str, chunk_size: int = 7) -> list[dict]:
        items: list[dict] = []
        for i in range(0, len(text), chunk_size):
            items.extend(parser.feed(text[i : i + chunk_size]))
        return items

    def test_incremental_scene_parsing(self) -> None:
        parser = StreamingJsonArrayParser(array_key="scenes")
        raw_items = self._feed_in_chunks(parser, SAMPLE_SCRIPT_JSON)

        self.assertEqual(len(raw_items), 2)
        scenes = [ScriptParser.parse_scene_item(item) for item in raw_items]
        self.assertEqual(scenes[0]["scene_number"], 1)
        self.assertEqual(scenes[0]["location"], "医院走廊")
        self.assertEqual(scenes[1]["scene_number"], 2)

    def test_incremental_storyboard_parsing(self) -> None:
        parser = StreamingJsonArrayParser(array_key="storyboard")
        raw_items = self._feed_in_chunks(parser, SAMPLE_STORYBOARD_JSON)

        self.assertEqual(len(raw_items), 2)
        shots = [ShotParser.parse_shot_item(item) for item in raw_items]
        self.assertEqual(shots[0]["shot_number"], 1)
        self.assertEqual(shots[1]["shot_size"], "close_up")

    def test_markdown_code_block_wrapped_response(self) -> None:
        wrapped = f"```json\n{SAMPLE_SCRIPT_JSON}\n```"
        parser = StreamingJsonArrayParser(array_key="scenes")
        raw_items = self._feed_in_chunks(parser, wrapped, chunk_size=11)

        self.assertEqual(len(raw_items), 2)

    def test_string_with_braces_does_not_break_parsing(self) -> None:
        payload = """{
  "scenes": [
    {
      "scene_number": 1,
      "location_type": "interior",
      "location": "测试",
      "time_type": "day",
      "time_detail": "",
      "content": "他说：{你好}，然后离开。"
    }
  ]
}"""
        parser = StreamingJsonArrayParser(array_key="scenes")
        raw_items = self._feed_in_chunks(parser, payload, chunk_size=5)

        self.assertEqual(len(raw_items), 1)
        scene = ScriptParser.parse_scene_item(raw_items[0])
        self.assertIn("{你好}", scene["content"])

    def test_partial_chunk_waits_for_complete_object(self) -> None:
        parser = StreamingJsonArrayParser(array_key="scenes")
        first_half = SAMPLE_SCRIPT_JSON[:80]
        second_half = SAMPLE_SCRIPT_JSON[80:]

        first_items = parser.feed(first_half)
        self.assertEqual(first_items, [])

        all_items = parser.feed(second_half)
        self.assertEqual(len(all_items), 2)


SAMPLE_CHARACTERS_JSON = """{
  "characters": [
    {
      "name": "李探长",
      "ref_code": "CHAR_A",
      "description": "45岁男性",
      "voice_tone": "低沉男声"
    },
    {
      "name": "小王",
      "ref_code": "CHAR_B",
      "description": "28岁男性",
      "voice_tone": "年轻男声"
    }
  ]
}"""


class TestCharacterStreamingJsonArrayParser(unittest.TestCase):
    def _feed_in_chunks(self, parser: StreamingJsonArrayParser, text: str, chunk_size: int = 7) -> list[dict]:
        items: list[dict] = []
        for i in range(0, len(text), chunk_size):
            items.extend(parser.feed(text[i : i + chunk_size]))
        return items

    def test_incremental_character_parsing(self) -> None:
        from utils.character_parser import CharacterParser

        parser = StreamingJsonArrayParser(array_key="characters")
        raw_items = self._feed_in_chunks(parser, SAMPLE_CHARACTERS_JSON)

        self.assertEqual(len(raw_items), 2)
        chars = [CharacterParser.parse_character_item(item) for item in raw_items]
        self.assertEqual(chars[0]["ref_code"], "CHAR_A")
        self.assertEqual(chars[1]["name"], "小王")


if __name__ == "__main__":
    unittest.main()
