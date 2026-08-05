import unittest
from utils.script_parser import ScriptParser
from models.enums import SceneLocation, SceneTime


class TestScriptParser(unittest.TestCase):
    def test_parse_normal_json(self):
        """测试正常的 JSON 格式解析"""
        json_input = '''
        {
          "title": "测试剧本",
          "scenes": [
            {
              "scene_number": 1,
              "location_type": "interior",
              "location": "审讯室",
              "time_type": "night",
              "time_detail": "",
              "content": "警察坐在桌前。"
            }
          ]
        }
        '''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(title, "测试剧本")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["scene_number"], 1)
        self.assertEqual(scenes[0]["location_type"], SceneLocation.INTERIOR.value)
        self.assertEqual(scenes[0]["location"], "审讯室")
        self.assertEqual(scenes[0]["time_type"], SceneTime.NIGHT.value)
        self.assertEqual(scenes[0]["content"], "警察坐在桌前。")

    def test_parse_markdown_wrapped_json(self):
        """测试 Markdown 代码块包裹的 JSON 解析"""
        json_input = '''```json
        {
          "title": "测试剧本",
          "scenes": []
        }
        ```'''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(title, "测试剧本")
        self.assertEqual(len(scenes), 0)

    def test_parse_markdown_wrapped_no_lang(self):
        """测试无语言标记的 Markdown 代码块"""
        json_input = '''```
        {
          "title": "无语言标记",
          "scenes": []
        }
        ```'''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(title, "无语言标记")

    def test_enum_mapping(self):
        """测试枚举值映射"""
        json_input = '''
        {
          "title": "枚举测试",
          "scenes": [
            {
              "scene_number": 1,
              "location_type": "exterior",
              "location": "街道",
              "time_type": "day",
              "time_detail": "",
              "content": "阳光明媚"
            },
            {
              "scene_number": 2,
              "location_type": "interior_exterior",
              "location": "门口",
              "time_type": "dusk",
              "time_detail": "黄昏时分",
              "content": "夕阳西下"
            }
          ]
        }
        '''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(scenes[0]["location_type"], SceneLocation.EXTERIOR.value)
        self.assertEqual(scenes[0]["time_type"], SceneTime.DAY.value)
        self.assertEqual(scenes[1]["location_type"], SceneLocation.INTERIOR_EXTERIOR.value)
        self.assertEqual(scenes[1]["time_type"], SceneTime.DUSK.value)
        self.assertEqual(scenes[1]["time_detail"], "黄昏时分")

    def test_missing_fields_with_defaults(self):
        """测试缺失字段容错（使用默认值）"""
        json_input = '''
        {
          "title": "缺失字段测试",
          "scenes": [
            {
              "scene_number": 1
            }
          ]
        }
        '''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["scene_number"], 1)
        self.assertEqual(scenes[0]["location_type"], SceneLocation.INTERIOR.value)
        self.assertEqual(scenes[0]["location"], "")
        self.assertEqual(scenes[0]["time_type"], SceneTime.DAY.value)
        self.assertEqual(scenes[0]["time_detail"], "")
        self.assertEqual(scenes[0]["content"], "")

    def test_invalid_json(self):
        """测试无效 JSON 格式抛出异常"""
        with self.assertRaises(ValueError) as context:
            ScriptParser.parse("这不是 JSON")
        self.assertIn("无效的 JSON 格式", str(context.exception))

    def test_invalid_enum_uses_default(self):
        """测试无效枚举值使用默认值"""
        json_input = '''
        {
          "title": "无效枚举测试",
          "scenes": [
            {
              "scene_number": 1,
              "location_type": "invalid_type",
              "location": "某处",
              "time_type": "invalid_time",
              "time_detail": "",
              "content": "内容"
            }
          ]
        }
        '''
        title, scenes = ScriptParser.parse(json_input)
        self.assertEqual(scenes[0]["location_type"], SceneLocation.INTERIOR.value)
        self.assertEqual(scenes[0]["time_type"], SceneTime.DAY.value)


if __name__ == "__main__":
    unittest.main()
