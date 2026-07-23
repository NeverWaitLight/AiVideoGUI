"""测试 CharacterService.extract_fixed_traits 固定特征提取逻辑。"""

import unittest

from service.character_service import CharacterService


class TestExtractFixedTraits(unittest.TestCase):
    """验证从结构化角色描述中正确提取固定特征。"""

    STRUCTURED_DESC = (
        "[外貌] 25岁女性，瓜子脸，柳叶眉，薄唇\n"
        "[发型] 齐肩黑色直发，中分\n"
        "[发色] 自然黑\n"
        "[瞳色] 深棕色\n"
        "[体型] 165cm，纤细匀称\n"
        "[上装] 白色棉质衬衫，袖口卷起\n"
        "[裤子] 深蓝色高腰牛仔裤\n"
        "[鞋袜] 白色帆布鞋，无袜\n"
        "[帽子] 无"
    )

    def test_extracts_only_fixed_traits(self):
        """只返回固定特征，不包含服装信息。"""
        result = CharacterService.extract_fixed_traits(self.STRUCTURED_DESC)
        self.assertIn("25岁女性", result)
        self.assertIn("齐肩黑色直发", result)
        self.assertIn("自然黑", result)
        self.assertIn("深棕色", result)
        self.assertIn("165cm", result)
        # 不应包含服装信息
        self.assertNotIn("衬衫", result)
        self.assertNotIn("牛仔裤", result)
        self.assertNotIn("帆布鞋", result)
        self.assertNotIn("贝雷帽", result)

    def test_empty_description(self):
        """空描述返回空字符串。"""
        self.assertEqual(CharacterService.extract_fixed_traits(""), "")
        self.assertEqual(CharacterService.extract_fixed_traits(None), "")

    def test_unstructured_description_fallback(self):
        """非结构化描述回退返回原文。"""
        old_desc = "25岁女性，齐肩黑发，穿白色衬衫和牛仔裤"
        result = CharacterService.extract_fixed_traits(old_desc)
        self.assertEqual(result, old_desc)

    def test_partial_fixed_traits(self):
        """只有部分固定特征时也能正确提取。"""
        desc = "[外貌] 30岁男性，方脸\n[体型] 180cm，健壮\n[上装] 黑色西装"
        result = CharacterService.extract_fixed_traits(desc)
        self.assertIn("30岁男性", result)
        self.assertIn("180cm", result)
        self.assertNotIn("西装", result)

    def test_traits_joined_by_comma(self):
        """多个固定特征用中文逗号连接。"""
        desc = "[外貌] 25岁女性\n[发色] 棕色"
        result = CharacterService.extract_fixed_traits(desc)
        self.assertEqual(result, "25岁女性，棕色")

    def test_with_clothing_only(self):
        """只有服装标签时返回空字符串。"""
        desc = "[上装] 白色衬衫\n[裤子] 蓝色牛仔裤"
        result = CharacterService.extract_fixed_traits(desc)
        self.assertEqual(result, "")

    def test_whitespace_handling(self):
        """正确处理多余空白。"""
        desc = "  [外貌]   25岁女性  \n  [发型]   黑色长发  "
        result = CharacterService.extract_fixed_traits(desc)
        self.assertIn("25岁女性", result)
        self.assertIn("黑色长发", result)


if __name__ == "__main__":
    unittest.main()
