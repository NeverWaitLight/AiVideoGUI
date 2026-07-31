import unittest
from service.character_service import CharacterService


class TestCharacterSpeciesTrait(unittest.TestCase):

    def test_extract_fixed_traits_with_species(self):
        description = """[物种] 人类-黄种人
[外貌] 25岁女性，瓜子脸，柳叶眉
[发型] 齐肩黑色直发，中分
[发色] 自然黑
[瞳色] 深棕色
[体型] 165cm，纤细匀称
[上装] 白色棉质衬衫
[裤子] 深蓝色高腰牛仔裤
[鞋袜] 白色帆布鞋
[帽子] 无"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertIn("人类-黄种人", result)
        self.assertIn("25岁女性，瓜子脸，柳叶眉", result)
        self.assertIn("齐肩黑色直发，中分", result)
        self.assertIn("自然黑", result)
        self.assertIn("深棕色", result)
        self.assertIn("165cm，纤细匀称", result)
        self.assertNotIn("白色棉质衬衫", result)
        self.assertNotIn("深蓝色高腰牛仔裤", result)

    def test_extract_fixed_traits_animal_species(self):
        description = """[物种] 动物（橘猫）
[外貌] 圆脸，大眼睛
[发型] 短毛，毛茸茸的感觉
[发色] 橘色
[瞳色] 黄绿色
[体型] 中等体型，肌肉感
[上装] 无
[裤子] 无
[鞋袜] 无
[帽子] 无"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertIn("动物（橘猫）", result)
        self.assertIn("圆脸，大眼睛", result)
        self.assertIn("短毛，毛茸茸的感觉", result)

    def test_extract_fixed_traits_anthropomorphic_species(self):
        description = """[物种] 拟人化动物（兔子）
[外貌] 30岁男性，长耳朵，粉色鼻子
[发型] 白色长毛，竖起的耳朵
[发色] 纯白色
[瞳色] 红色
[体型] 180cm，纤细挺拔
[上装] 黑色西装
[裤子] 黑色西裤
[鞋袜] 黑色皮鞋
[帽子] 黑色礼帽"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertIn("拟人化动物（兔子）", result)
        self.assertIn("30岁男性，长耳朵，粉色鼻子", result)
        self.assertNotIn("黑色西装", result)
        self.assertNotIn("黑色礼帽", result)

    def test_extract_fixed_traits_white_human_species(self):
        description = """[物种] 人类-白人
[外貌] 35岁男性，方形脸，深邃五官
[发型] 短发，侧分
[发色] 金色
[瞳色] 蓝色
[体型] 185cm，壮实体格
[上装] 灰色T恤
[裤子] 牛仔裤
[鞋袜] 运动鞋
[帽子] 无"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertIn("人类-白人", result)
        self.assertIn("35岁男性，方形脸，深邃五官", result)
        self.assertIn("金色", result)
        self.assertIn("蓝色", result)

    def test_extract_fixed_traits_black_human_species(self):
        description = """[物种] 人类-黑人
[外貌] 28岁女性，圆脸，丰满嘴唇
[发型] 爆炸头
[发色] 黑色
[瞳色] 深棕色
[体型] 170cm，健美身材
[上装] 红色背心
[裤子] 黑色紧身裤
[鞋袜] 白色运动鞋
[帽子] 无"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertIn("人类-黑人", result)
        self.assertIn("28岁女性，圆脸，丰满嘴唇", result)

    def test_species_tag_is_first(self):
        description = """[物种] 人类-黄种人
[外貌] 25岁女性
[发型] 长发
[发色] 黑色
[瞳色] 棕色
[体型] 165cm"""

        result = CharacterService.extract_fixed_traits(description)

        self.assertTrue(result.startswith("人类-黄种人"))


if __name__ == "__main__":
    unittest.main()
