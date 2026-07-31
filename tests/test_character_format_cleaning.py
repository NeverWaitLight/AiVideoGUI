import unittest
from service.character_service import CharacterService


class TestCharacterFormatCleaning(unittest.TestCase):

    def test_clean_html_br_tags(self):
        text = "短发，毛茸茸的感觉<br>橘色<br>黄绿色"
        cleaned = CharacterService._clean_format_markers(text)
        self.assertEqual(cleaned, "短发，毛茸茸的感觉 橘色 黄绿色")
        self.assertNotIn("<br>", cleaned)

    def test_clean_html_tags(self):
        test_cases = [
            ("<b>粗体文本</b>", "粗体文本"),
            ("<i>斜体文本</i>", "斜体文本"),
            ("<strong>强调文本</strong>", "强调文本"),
            ("<em>强调文本</em>", "强调文本"),
            ("<span>普通文本</span>", "普通文本"),
            ("文本<br/>换行", "文本 换行"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                cleaned = CharacterService._clean_format_markers(input_text)
                self.assertEqual(cleaned, expected)

    def test_clean_markdown_bold(self):
        test_cases = [
            ("**粗体文本**", "粗体文本"),
            ("__粗体文本__", "粗体文本"),
            ("普通文本**粗体**继续", "普通文本粗体继续"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                cleaned = CharacterService._clean_format_markers(input_text)
                self.assertEqual(cleaned, expected)

    def test_clean_markdown_italic(self):
        test_cases = [
            ("*斜体文本*", "斜体文本"),
            ("_斜体文本_", "斜体文本"),
            ("普通文本*斜体*继续", "普通文本斜体继续"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                cleaned = CharacterService._clean_format_markers(input_text)
                self.assertEqual(cleaned, expected)

    def test_clean_markdown_headers(self):
        test_cases = [
            ("# 一级标题", "一级标题"),
            ("## 二级标题", "二级标题"),
            ("### 三级标题", "三级标题"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                cleaned = CharacterService._clean_format_markers(input_text)
                self.assertEqual(cleaned, expected)

    def test_clean_mixed_formats(self):
        text = "25岁男性<br>**圆脸**，大眼睛<br>*短胡须*，尖耳朵"
        cleaned = CharacterService._clean_format_markers(text)

        self.assertNotIn("<br>", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("*", cleaned)

        self.assertIn("25岁男性", cleaned)
        self.assertIn("圆脸", cleaned)
        self.assertIn("大眼睛", cleaned)
        self.assertIn("短胡须", cleaned)
        self.assertIn("尖耳朵", cleaned)

    def test_clean_complex_character_description(self):
        text = "[角色形象] CHAR_A：25岁男性，圆脸，大眼睛，短胡须，尖耳朵<br>[发型] 短发，毛茸茸的感觉<br>[发色] 橘色<br>[瞳色] 黄绿色<br>[体型] 170cm，中等身材"
        cleaned = CharacterService._clean_format_markers(text)

        self.assertNotIn("<br>", cleaned)

        self.assertIn("[角色形象]", cleaned)
        self.assertIn("25岁男性", cleaned)
        self.assertIn("短发，毛茸茸的感觉", cleaned)
        self.assertIn("橘色", cleaned)

    def test_clean_whitespace_normalization(self):
        text = "文本1<br>  文本2<br><br>文本3"
        cleaned = CharacterService._clean_format_markers(text)

        self.assertNotIn("  ", cleaned)

        self.assertEqual(cleaned, "文本1 文本2 文本3")

    def test_clean_empty_string(self):
        self.assertEqual(CharacterService._clean_format_markers(""), "")
        self.assertEqual(CharacterService._clean_format_markers(None), None)

    def test_clean_no_format_markers(self):
        text = "普通文本，没有任何格式标记"
        cleaned = CharacterService._clean_format_markers(text)
        self.assertEqual(cleaned, text)

    def test_preserve_normal_underscores(self):
        text = "变量名_test_value是一个标识符"
        cleaned = CharacterService._clean_format_markers(text)
        self.assertIn("test", cleaned)


if __name__ == "__main__":
    unittest.main()
