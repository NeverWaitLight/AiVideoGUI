"""测试 ScriptParser → batch_create_scenes → DB 的枚举转换链路。"""

import unittest

from models.data_models import SceneLocation, SceneTime
from utils.script_parser import ScriptParser


class TestScriptParserEnumValues(unittest.TestCase):
    """ScriptParser 输出的枚举值应为字符串（.value），而非枚举实例。"""

    SAMPLE_SCRIPT = """迷雾之城

第1场  内景  审讯室  -  夜

昏暗的审讯室内，一盏台灯照亮桌面。

警官
（低声）
你还有什么要说的？

第2场  外景  老城区街道  -  黄昏

雨后的街道，霓虹灯倒映在积水中。

第3场  内景/外景  天台  -  晨

晨光中，城市天际线渐渐清晰。

剧终
"""

    def test_parse_returns_string_location_type(self):
        """解析结果的 location_type 应为字符串。"""
        title, scenes = ScriptParser.parse(self.SAMPLE_SCRIPT)
        self.assertEqual(title, "迷雾之城")
        self.assertEqual(len(scenes), 3)

        for scene in scenes:
            self.assertIsInstance(scene["location_type"], str)
            self.assertIn(scene["location_type"], ["interior", "exterior", "interior_exterior"])

    def test_parse_returns_string_time_type(self):
        """解析结果的 time_type 应为字符串。"""
        _, scenes = ScriptParser.parse(self.SAMPLE_SCRIPT)
        for scene in scenes:
            self.assertIsInstance(scene["time_type"], str)

    def test_parse_scene_values(self):
        """验证各场次的值正确。"""
        _, scenes = ScriptParser.parse(self.SAMPLE_SCRIPT)

        self.assertEqual(scenes[0]["location_type"], "interior")
        self.assertEqual(scenes[0]["time_type"], "night")

        self.assertEqual(scenes[1]["location_type"], "exterior")
        self.assertEqual(scenes[1]["time_type"], "dusk")

        self.assertEqual(scenes[2]["location_type"], "interior_exterior")
        self.assertEqual(scenes[2]["time_type"], "dawn")

    def test_enum_reconstruction_from_parsed_values(self):
        """从解析结果的字符串值能正确重建枚举实例。"""
        _, scenes = ScriptParser.parse(self.SAMPLE_SCRIPT)
        for scene in scenes:
            loc = SceneLocation(scene["location_type"])
            self.assertIsInstance(loc, SceneLocation)

            time = SceneTime(scene["time_type"])
            self.assertIsInstance(time, SceneTime)


class TestSceneEntityEnumConversion(unittest.TestCase):
    """SceneRepository 的 _to_entity / _to_dto 应正确处理枚举与字符串的转换。"""

    def test_to_entity_with_enum(self):
        """DTO 含枚举实例时，Entity 应存储字符串值。"""
        from datetime import datetime
        from models.data_models import Scene
        from storage.repositories.script import SceneRepository

        scene = Scene(
            id="test-1",
            script_id="script-1",
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="审讯室",
            time_type=SceneTime.NIGHT,
            time_detail="",
            content="测试内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repo = SceneRepository.__new__(SceneRepository)
        entity = repo._to_entity(scene)

        self.assertEqual(entity.location_type, "interior")
        self.assertEqual(entity.time_type, "night")
        self.assertIsInstance(entity.location_type, str)
        self.assertIsInstance(entity.time_type, str)

    def test_to_entity_with_string(self):
        """DTO 含字符串时，Entity 应原样传递字符串。"""
        from datetime import datetime
        from models.data_models import Scene
        from storage.repositories.script import SceneRepository

        scene = Scene(
            id="test-2",
            script_id="script-1",
            scene_number=2,
            location_type="exterior",
            location="街道",
            time_type="day",
            time_detail="",
            content="测试内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repo = SceneRepository.__new__(SceneRepository)
        entity = repo._to_entity(scene)

        self.assertEqual(entity.location_type, "exterior")
        self.assertEqual(entity.time_type, "day")

    def test_to_dto_with_string_entity(self):
        """Entity 的字符串字段应正确转换为 DTO 的枚举实例。"""
        from datetime import datetime
        from storage.orm.models import SceneEntity
        from storage.repositories.script import SceneRepository

        entity = SceneEntity(
            id="test-3",
            script_id="script-1",
            scene_number=3,
            location_type="interior_exterior",
            location="天台",
            time_type="dawn",
            time_detail="",
            content="测试内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repo = SceneRepository.__new__(SceneRepository)
        dto = repo._to_dto(entity)

        self.assertIsInstance(dto.location_type, SceneLocation)
        self.assertEqual(dto.location_type, SceneLocation.INTERIOR_EXTERIOR)
        self.assertIsInstance(dto.time_type, SceneTime)
        self.assertEqual(dto.time_type, SceneTime.DAWN)


if __name__ == "__main__":
    unittest.main()
