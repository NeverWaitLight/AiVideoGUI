import unittest
from utils.character_parser import CharacterParser


class TestCharacterParser(unittest.TestCase):
    def test_parse_json_array(self):
        """测试 JSON 数组格式解析"""
        json_input = '''
        [
          {
            "name": "李明",
            "ref_code": "CHAR_A",
            "description": "30岁男性，短发"
          },
          {
            "name": "王芳",
            "ref_code": "CHAR_B",
            "description": "25岁女性，长发"
          }
        ]
        '''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "李明")
        self.assertEqual(result[0]["ref_code"], "CHAR_A")
        self.assertEqual(result[0]["description"], "30岁男性，短发")
        self.assertEqual(result[1]["name"], "王芳")
        self.assertEqual(result[1]["ref_code"], "CHAR_B")

    def test_parse_characters_object(self):
        """测试 {"characters": [...]} 对象格式解析"""
        json_input = '''
        {
          "characters": [
            {
              "name": "张伟",
              "ref_code": "CHAR_A",
              "description": "40岁男性"
            }
          ]
        }
        '''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "张伟")
        self.assertEqual(result[0]["ref_code"], "CHAR_A")
        self.assertEqual(result[0]["description"], "40岁男性")

    def test_parse_markdown_wrapped_json(self):
        """测试 Markdown 代码块包裹的 JSON 解析"""
        json_input = '''```json
        [
          {
            "name": "李明",
            "ref_code": "CHAR_A",
            "description": "30岁男性"
          }
        ]
        ```'''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "李明")

    def test_chinese_key_fallback(self):
        """测试中文键名 fallback — 角色名, 引用代号, 形象描述"""
        json_input = '''
        [
          {
            "角色名": "李明",
            "引用代号": "CHAR_A",
            "形象描述": "30岁男性，短发"
          }
        ]
        '''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "李明")
        self.assertEqual(result[0]["ref_code"], "CHAR_A")
        self.assertEqual(result[0]["description"], "30岁男性，短发")

    def test_missing_fields_skips_character(self):
        """测试缺失字段容错 — name/ref_code 为空则跳过该角色"""
        json_input = '''
        [
          {
            "name": "",
            "ref_code": "CHAR_A",
            "description": "无名角色"
          },
          {
            "name": "李明",
            "ref_code": "",
            "description": "无代号角色"
          },
          {
            "name": "王芳",
            "ref_code": "CHAR_B",
            "description": "有效角色"
          }
        ]
        '''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "王芳")
        self.assertEqual(result[0]["ref_code"], "CHAR_B")

    def test_invalid_format_raises_value_error(self):
        """测试无效格式抛出 ValueError"""
        with self.assertRaises(ValueError):
            CharacterParser.parse("这不是 JSON，也没有任何 JSON 结构")

    def test_mixed_valid_and_invalid(self):
        """测试混合有效和无效数据 — 只保留有效角色"""
        json_input = '''
        [
          {
            "name": "李明",
            "ref_code": "CHAR_A",
            "description": "有效"
          },
          "invalid_string_item",
          {
            "description": "缺少 name 和 ref_code"
          },
          {
            "name": "王芳",
            "ref_code": "CHAR_B",
            "description": "也有效"
          }
        ]
        '''
        result = CharacterParser.parse(json_input)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "李明")
        self.assertEqual(result[1]["name"], "王芳")

    def test_parse_character_item_valid(self) -> None:
        item = {
            "name": "李明",
            "ref_code": "CHAR_A",
            "description": "30岁男性",
            "voice_tone": "低沉男声",
        }
        parsed = CharacterParser.parse_character_item(item)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["name"], "李明")
        self.assertEqual(parsed["voice_tone"], "低沉男声")

    def test_parse_character_item_invalid_returns_none(self) -> None:
        parsed = CharacterParser.parse_character_item({"name": "", "ref_code": "CHAR_A"})
        self.assertIsNone(parsed)


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


class TestCharacterStreamingParser(unittest.TestCase):
    def _feed_in_chunks(self, text: str, chunk_size: int = 7) -> list[dict]:
        from utils.streaming_json_array_parser import StreamingJsonArrayParser

        parser = StreamingJsonArrayParser(array_key="characters")
        items: list[dict] = []
        for i in range(0, len(text), chunk_size):
            items.extend(parser.feed(text[i : i + chunk_size]))
        return items

    def test_incremental_character_parsing(self) -> None:
        raw_items = self._feed_in_chunks(SAMPLE_CHARACTERS_JSON)
        self.assertEqual(len(raw_items), 2)
        chars = [CharacterParser.parse_character_item(item) for item in raw_items]
        self.assertEqual(chars[0]["ref_code"], "CHAR_A")
        self.assertEqual(chars[1]["name"], "小王")


if __name__ == "__main__":
    unittest.main()
