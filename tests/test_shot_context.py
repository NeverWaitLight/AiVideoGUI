"""测试 inject_shot_context 前后镜头上下文注入逻辑。"""

import unittest

from utils.prompt_builder import inject_shot_context


class TestInjectShotContext(unittest.TestCase):
    """验证前后镜头参考正确插入到增强后的提示词中。"""

    def test_both_contexts_with_character_and_scene_tag(self):
        """角色增强后的提示词含 [画面] 标记时，上下文插入到 [画面] 之前。"""
        prompt = "[角色形象] CHAR_A：25岁女性，齐肩黑发\n[画面] CHAR_A 站在天桥上"
        prev_ctx = "[前一镜头参考] 场1镜2：CHAR_A 走出咖啡馆（仅供参考，保持动作和场景连贯性，不要复现此画面）"
        next_ctx = "[后一镜头参考] 场1镜4：CHAR_A 转身回望（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context(prompt, prev_ctx, next_ctx)

        self.assertIn("[前一镜头参考]", result)
        self.assertIn("[后一镜头参考]", result)
        # 上下文应在 [画面] 之前
        prev_pos = result.index("[前一镜头参考]")
        next_pos = result.index("[后一镜头参考]")
        scene_pos = result.index("[画面]")
        self.assertLess(prev_pos, scene_pos)
        self.assertLess(next_pos, scene_pos)
        # 角色形象应在最前
        char_pos = result.index("[角色形象]")
        self.assertLess(char_pos, prev_pos)

    def test_only_prev_context(self):
        """只有前一镜头参考时正确插入。"""
        prompt = "[画面] CHAR_A 走在街道上"
        prev_ctx = "[前一镜头参考] 场1镜1：CHAR_A 出门（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context(prompt, prev_ctx, "")

        self.assertIn("[前一镜头参考]", result)
        self.assertNotIn("[后一镜头参考]", result)
        self.assertIn("[画面]", result)

    def test_only_next_context(self):
        """只有后一镜头参考时正确插入。"""
        prompt = "[画面] CHAR_A 出门"
        next_ctx = "[后一镜头参考] 场1镜3：CHAR_A 走在街道上（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context(prompt, "", next_ctx)

        self.assertNotIn("[前一镜头参考]", result)
        self.assertIn("[后一镜头参考]", result)

    def test_no_context_returns_prompt_unchanged(self):
        """无上下文时原样返回。"""
        prompt = "[角色形象] CHAR_A：25岁女性\n[画面] CHAR_A 站在天桥上"

        result = inject_shot_context(prompt, "", "")

        self.assertEqual(result, prompt)

    def test_no_scene_tag_appends_to_end(self):
        """无 [画面] 标记时追加到末尾。"""
        prompt = "CHAR_A 站在天桥上，俯瞰城市车流"
        prev_ctx = "[前一镜头参考] 场1镜1：CHAR_A 走出门（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context(prompt, prev_ctx, "")

        self.assertTrue(result.startswith(prompt))
        self.assertIn("[前一镜头参考]", result)

    def test_empty_prompt_with_context(self):
        """空提示词也能正确处理上下文。"""
        prev_ctx = "[前一镜头参考] 场1镜1：CHAR_A 走出门（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context("", prev_ctx, "")

        self.assertIn("[前一镜头参考]", result)

    def test_multiple_scene_tags_only_first_replaced(self):
        """提示词含多个 [画面] 时只替换第一个。"""
        prompt = "[画面] 第一个场景 [画面] 第二个场景"
        prev_ctx = "[前一镜头参考] 场1镜1：前一个镜头（仅供参考，保持动作和场景连贯性，不要复现此画面）"

        result = inject_shot_context(prompt, prev_ctx, "")

        # 第一个 [画面] 被替换，第二个保留
        self.assertEqual(result.count("[画面]"), 2)


if __name__ == "__main__":
    unittest.main()
