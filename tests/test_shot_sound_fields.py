"""测试分镜解析器的声音字段提取"""

import unittest
from utils.shot_parser import ShotParser


class TestShotSoundFields(unittest.TestCase):
    def test_parse_all_sound_fields(self):
        """测试解析器能够正确提取所有声音字段"""
        storyboard_json = """
        {
            "storyboard": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_size": "medium_shot",
                    "camera_movement": "固定镜头",
                    "content": "测试内容",
                    "sound_effect": "脚步声，清脆的敲击声",
                    "ambient_sound": "树叶沙沙声、远处鸟鸣",
                    "background_music": "柔和的木吉他音乐",
                    "duration": 5.0,
                    "notes": "暖色调"
                }
            ]
        }
        """

        shots = ShotParser.parse(storyboard_json)

        self.assertEqual(len(shots), 1)
        shot = shots[0]

        self.assertEqual(shot["sound_effect"], "脚步声，清脆的敲击声")
        self.assertEqual(shot["ambient_sound"], "树叶沙沙声、远处鸟鸣")
        self.assertEqual(shot["background_music"], "柔和的木吉他音乐")

    def test_parse_empty_sound_fields(self):
        """测试解析器能够处理空的声音字段（继承场次设定）"""
        storyboard_json = """
        {
            "storyboard": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_size": "close_up",
                    "camera_movement": "固定镜头",
                    "content": "测试内容",
                    "sound_effect": "",
                    "ambient_sound": "",
                    "background_music": "",
                    "duration": 3.0,
                    "notes": ""
                }
            ]
        }
        """

        shots = ShotParser.parse(storyboard_json)

        self.assertEqual(len(shots), 1)
        shot = shots[0]

        self.assertEqual(shot["sound_effect"], "")
        self.assertEqual(shot["ambient_sound"], "")
        self.assertEqual(shot["background_music"], "")

    def test_parse_dialogue_with_sound_effects(self):
        """测试解析器能够同时处理对话和音效"""
        storyboard_json = """
        {
            "storyboard": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_size": "medium_shot",
                    "camera_movement": "固定镜头",
                    "content": "人物说话",
                    "dialogue": "测试对话",
                    "sound_effect": "他低声说：'我们不能再装作一切没变。'",
                    "ambient_sound": "远处传来模糊的街道车流声",
                    "background_music": "低沉的大提琴旋律",
                    "duration": 6.0,
                    "notes": "暖色调"
                }
            ]
        }
        """

        shots = ShotParser.parse(storyboard_json)

        self.assertEqual(len(shots), 1)
        shot = shots[0]

        self.assertEqual(shot["dialogue"], "测试对话")
        self.assertEqual(shot["sound_effect"], "他低声说：'我们不能再装作一切没变。'")
        self.assertEqual(shot["ambient_sound"], "远处传来模糊的街道车流声")
        self.assertEqual(shot["background_music"], "低沉的大提琴旋律")

    def test_parse_missing_sound_fields(self):
        """测试解析器能够处理缺失的声音字段（向后兼容）"""
        storyboard_json = """
        {
            "storyboard": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_size": "full_shot",
                    "camera_movement": "固定镜头",
                    "content": "测试内容",
                    "duration": 4.0,
                    "notes": ""
                }
            ]
        }
        """

        shots = ShotParser.parse(storyboard_json)

        self.assertEqual(len(shots), 1)
        shot = shots[0]

        # 缺失的字段应该被填充为空字符串
        self.assertEqual(shot["sound_effect"], "")
        self.assertEqual(shot["ambient_sound"], "")
        self.assertEqual(shot["background_music"], "")
        self.assertEqual(shot["dialogue"], "")


if __name__ == "__main__":
    unittest.main()
