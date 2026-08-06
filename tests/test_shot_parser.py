import unittest
from utils.shot_parser import ShotParser
from models.enums import ShotSize


class TestShotParser(unittest.TestCase):
    def test_parse_normal_json(self):
        """测试正常 JSON 格式解析"""
        json_input = '''
        {
          "storyboard": [
            {
              "scene_number": 1,
              "shot_number": 1,
              "shot_size": "close_up",
              "camera_movement": "推",
              "content": "主角面部特写",
              "dialogue": "我不信。",
              "sound_effect": "心跳声",
              "duration": 3.5,
              "notes": "注意灯光"
            }
          ]
        }
        '''
        shots = ShotParser.parse(json_input)
        self.assertEqual(len(shots), 1)

        shot = shots[0]
        self.assertEqual(shot["scene_number"], 1)
        self.assertEqual(shot["shot_number"], 1)
        self.assertEqual(shot["shot_size"], ShotSize.CLOSE_UP.value)
        self.assertEqual(shot["camera_movement"], "推")
        self.assertEqual(shot["content"], "主角面部特写")
        self.assertEqual(shot["dialogue"], "我不信。")
        self.assertEqual(shot["sound_effect"], "心跳声")
        self.assertEqual(shot["duration"], 3.5)
        self.assertEqual(shot["notes"], "注意灯光")

    def test_parse_markdown_wrapped_json(self):
        """测试 Markdown 代码块包裹的 JSON 解析"""
        json_input = '''```json
        {
          "storyboard": [
            {
              "scene_number": 1,
              "shot_number": 1,
              "shot_size": "medium_shot",
              "camera_movement": "",
              "content": "全景",
              "dialogue": "",
              "sound_effect": "",
              "duration": 2.0,
              "notes": ""
            }
          ]
        }
        ```'''
        shots = ShotParser.parse(json_input)
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0]["shot_size"], ShotSize.MEDIUM_SHOT.value)

    def test_shot_size_enum_mapping(self):
        """测试 6 个有效 shot_size 枚举值映射"""
        all_sizes = [
            ("extreme_close_up", ShotSize.EXTREME_CLOSE_UP),
            ("close_up", ShotSize.CLOSE_UP),
            ("medium_shot", ShotSize.MEDIUM_SHOT),
            ("full_shot", ShotSize.FULL_SHOT),
            ("long_shot", ShotSize.LONG_SHOT),
            ("extreme_long_shot", ShotSize.EXTREME_LONG_SHOT),
        ]
        for size_str, expected_enum in all_sizes:
            json_input = f'''
            {{
              "storyboard": [
                {{
                  "scene_number": 1,
                  "shot_number": 1,
                  "shot_size": "{size_str}",
                  "camera_movement": "",
                  "content": "",
                  "dialogue": "",
                  "sound_effect": "",
                  "duration": 1.0,
                  "notes": ""
                }}
              ]
            }}
            '''
            shots = ShotParser.parse(json_input)
            self.assertEqual(
                shots[0]["shot_size"],
                expected_enum.value,
                f"shot_size '{size_str}' 应映射为 {expected_enum.value}",
            )

    def test_unrecognized_shot_size_falls_back(self):
        """测试未识别的 shot_size 回退到 medium_shot"""
        json_input = '''
        {
          "storyboard": [
            {
              "scene_number": 1,
              "shot_number": 1,
              "shot_size": "unknown_size",
              "camera_movement": "",
              "content": "",
              "dialogue": "",
              "sound_effect": "",
              "duration": 1.0,
              "notes": ""
            }
          ]
        }
        '''
        shots = ShotParser.parse(json_input)
        self.assertEqual(shots[0]["shot_size"], ShotSize.MEDIUM_SHOT.value)

    def test_missing_fields_use_defaults(self):
        """测试缺失字段容错 — 部分字段缺失时使用默认值"""
        json_input = '''
        {
          "storyboard": [
            {
              "scene_number": 1,
              "shot_number": 2
            }
          ]
        }
        '''
        shots = ShotParser.parse(json_input)

        shot = shots[0]
        self.assertEqual(shot["scene_number"], 1)
        self.assertEqual(shot["shot_number"], 2)
        self.assertEqual(shot["shot_size"], ShotSize.MEDIUM_SHOT.value)
        self.assertEqual(shot["camera_movement"], "")
        self.assertEqual(shot["content"], "")
        self.assertEqual(shot["dialogue"], "")
        self.assertEqual(shot["sound_effect"], "")
        self.assertEqual(shot["duration"], 0.0)
        self.assertEqual(shot["notes"], "")

    def test_empty_storyboard(self):
        """测试空 storyboard 数组"""
        json_input = '''
        {
          "storyboard": []
        }
        '''
        shots = ShotParser.parse(json_input)
        self.assertEqual(shots, [])

    def test_invalid_json_raises_value_error(self):
        """测试无效 JSON 格式抛出 ValueError"""
        with self.assertRaises(ValueError) as context:
            ShotParser.parse("这不是 JSON")
        self.assertIn("无效的 JSON 格式", str(context.exception))

    def test_duration_int_to_float(self):
        """测试 duration 字段 int 转 float"""
        json_input = '''
        {
          "storyboard": [
            {
              "scene_number": 1,
              "shot_number": 1,
              "shot_size": "medium_shot",
              "camera_movement": "",
              "content": "",
              "dialogue": "",
              "sound_effect": "",
              "duration": 5,
              "notes": ""
            }
          ]
        }
        '''
        shots = ShotParser.parse(json_input)
        self.assertIsInstance(shots[0]["duration"], float)
        self.assertEqual(shots[0]["duration"], 5.0)

    def test_unescaped_newlines_in_string_values(self):
        """测试字符串值中包含未转义换行符时仍能解析"""
        json_input = '{\n  "storyboard": [\n    {\n      "scene_number": 1,\n      "shot_number": 1,\n      "shot_size": "medium_shot",\n      "camera_movement": "",\n      "content": "line1\nline2",\n      "dialogue": "",\n      "sound_effect": "",\n      "duration": 3.0,\n      "notes": ""\n    }\n  ]\n}'
        shots = ShotParser.parse(json_input)
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0]["content"], "line1\nline2")


if __name__ == "__main__":
    unittest.main()
