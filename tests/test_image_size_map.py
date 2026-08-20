import unittest

from service.image_service import resolve_image_size


class TestResolveImageSize(unittest.TestCase):
    def test_project_aspect_ratios(self) -> None:
        self.assertEqual(resolve_image_size("16:9"), "1696*960")
        self.assertEqual(resolve_image_size("9:16"), "960*1696")
        self.assertEqual(resolve_image_size("1:1"), "1280*1280")
        self.assertEqual(resolve_image_size("4:3"), "1472*1104")
        self.assertEqual(resolve_image_size("3:4"), "1104*1472")

    def test_unknown_ratio_falls_back_to_16_9(self) -> None:
        self.assertEqual(resolve_image_size(""), "1696*960")
        self.assertEqual(resolve_image_size("21:9"), "1696*960")


if __name__ == "__main__":
    unittest.main(verbosity=2)
