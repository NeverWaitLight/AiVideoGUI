import unittest
from pathlib import Path
from prompts.manager import PromptTemplate, PromptTemplateManager


class TestPromptTemplate(unittest.TestCase):

    def test_build_messages_without_few_shot(self):
        config = {
            "system_prompt": "你是一个助手",
            "user_prompt_template": "请回答：{question}",
        }
        template = PromptTemplate(config)
        messages = template.build_messages(question="什么是 AI？")

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "你是一个助手")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "请回答：什么是 AI？")

    def test_build_messages_with_few_shot(self):
        config = {
            "system_prompt": "你是一个助手",
            "few_shot_examples": [
                {"user": "你好", "assistant": "你好！有什么可以帮助你的吗？"},
                {"user": "介绍一下你自己", "assistant": "我是 AI 助手"},
            ],
            "user_prompt_template": "请回答：{question}",
        }
        template = PromptTemplate(config)
        messages = template.build_messages(question="什么是 AI？")

        self.assertEqual(len(messages), 6)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "你好")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["content"], "你好！有什么可以帮助你的吗？")
        self.assertEqual(messages[3]["role"], "user")
        self.assertEqual(messages[4]["role"], "assistant")
        self.assertEqual(messages[5]["role"], "user")
        self.assertEqual(messages[5]["content"], "请回答：什么是 AI？")


class TestPromptTemplateManager(unittest.TestCase):

    def test_load_templates(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        templates = manager.list_templates()
        self.assertGreater(len(templates), 0)
        self.assertIn("outline_optimize", templates)
        self.assertIn("storyboard_image_prompt", templates)

    def test_get_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("outline_optimize")
        self.assertIsInstance(template, PromptTemplate)
        self.assertIn("大纲", template.system_prompt)

    def test_get_nonexistent_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        with self.assertRaises(KeyError):
            manager.get_template("nonexistent_template")

    def test_outline_optimization_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("outline_optimize")
        messages = template.build_messages(
            original_content="这是原始大纲",
            user_requirement="增加悬疑元素",
        )

        self.assertGreater(len(messages), 0)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        last_message = messages[-1]["content"]
        self.assertIn("这是原始大纲", last_message)
        self.assertIn("增加悬疑元素", last_message)

    def test_all_templates_placeholder_contract(self):
        """遍历全部模板，用 dummy kwargs 调用 build_messages，验证占位符契约不破坏"""
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template_kwargs = {
            "outline_optimize": {"original_content": "大纲", "user_requirement": "要求"},
            "screenplay_generate": {"outline_content": "大纲"},
            "screenplay_optimize": {
                "outline_content": "大纲",
                "current_script": "剧本",
                "user_requirement": "要求",
            },
            "storyboard_generate": {"script_content": "剧本", "art_style": "写实"},
            "storyboard_optimize": {
                "outline_content": "大纲",
                "script_content": "剧本",
                "character_content": "角色",
                "current_storyboard": "分镜",
                "user_requirement": "要求",
            },
            "character_generate": {
                "outline_content": "大纲",
                "script_content": "剧本",
                "user_requirement": "要求",
            },
            "character_optimize": {
                "outline_content": "大纲",
                "script_content": "剧本",
                "current_characters": "角色",
                "user_requirement": "要求",
            },
            "character_refine": {
                "character_name": "角色名",
                "current_description": "描述",
                "user_requirement": "要求",
            },
            "storyboard_image_prompt": {
                "shot_size": "中景",
                "camera_movement": "固定",
                "content": "画面",
                "notes": "备注",
                "character_info": "角色",
                "visual_style_block": "【画面风格】风格\n\n【画面风格要求】\n风格要求\n",
            },
            "character_image_prompt": {
                "character_name": "角色名",
                "description": "描述",
                "visual_style_block": "【画面风格】风格\n\n【画面风格要求】\n风格要求\n",
                "user_requirement": "要求",
            },
            "project_cover_image_prompt": {
                "project_name": "项目名",
                "aspect_ratio": "16:9",
                "outline_content": "大纲",
                "character_info": "角色",
                "visual_style_block": "【视觉风格】风格\n\n【画面风格要求】\n风格要求\n",
            },
            "storyboard_video_prompt_clean": {"original_prompt": "原始提示词"},
        }

        loaded = set(manager.list_templates())
        self.assertEqual(
            set(template_kwargs.keys()),
            loaded,
            "测试用例的模板集合与实际加载的模板集合不一致",
        )

        for name, kwargs in template_kwargs.items():
            with self.subTest(template=name):
                template = manager.get_template(name)
                messages = template.build_messages(**kwargs)
                self.assertGreater(len(messages), 1)
                self.assertEqual(messages[0]["role"], "system")
                self.assertEqual(messages[-1]["role"], "user")
                for key, value in kwargs.items():
                    self.assertIn(
                        value,
                        messages[-1]["content"],
                        f"模板 {name} 的占位符 {{{key}}} 未被正确替换",
                    )


class TestChatPromptBuilderVisualStyle(unittest.TestCase):
    def setUp(self):
        from prompts.chat_prompt_builder import ChatPromptBuilder

        templates_dir = Path(__file__).resolve().parent.parent / "prompts" / "templates"
        self.builder = ChatPromptBuilder(PromptTemplateManager(templates_dir))

    def test_design_image_prompt_includes_style_when_set(self):
        messages = self.builder.build_design_image_prompt_messages(
            content="画面",
            visual_style="3D卡通",
        )
        user = messages[-1]["content"]
        system = messages[0]["content"]
        self.assertIn("【画面风格】3D卡通", user)
        self.assertIn("【画面风格要求】", user)
        self.assertIn("整体画面采用【3D卡通】风格", user)
        self.assertNotIn("纯黑白", user)
        self.assertNotIn("pure black and white", system)
        self.assertNotIn("英文提示词", system)
        self.assertIn("提示词", system)

    def test_design_image_prompt_omits_style_when_default_or_empty(self):
        for style in ("", "默认", "  ", None):
            with self.subTest(visual_style=style):
                messages = self.builder.build_design_image_prompt_messages(
                    content="画面",
                    visual_style=style or "",
                )
                user = messages[-1]["content"]
                self.assertNotIn("【画面风格】", user)
                self.assertNotIn("【画面风格要求】", user)
                self.assertNotIn("纯黑白", user)
                self.assertNotIn("无特殊风格要求", user)
                self.assertNotIn("只输出中文提示词", user)
                self.assertNotIn("不要输出英文", user)

    def test_character_design_image_prompt_includes_style_when_set(self):
        messages = self.builder.build_character_design_image_prompt_messages(
            character_name="李明",
            description="描述",
            visual_style="水彩插画",
        )
        user = messages[-1]["content"]
        self.assertIn("【画面风格】水彩插画", user)
        self.assertIn("【画面风格要求】", user)
        self.assertIn("整体画面采用【水彩插画】风格", user)

    def test_character_design_image_prompt_omits_style_when_default_or_empty(self):
        for style in ("", "默认", "  ", None):
            with self.subTest(visual_style=style):
                messages = self.builder.build_character_design_image_prompt_messages(
                    character_name="李明",
                    description="描述",
                    visual_style=style or "",
                )
                user = messages[-1]["content"]
                self.assertNotIn("【画面风格】", user)
                self.assertNotIn("【画面风格要求】", user)
                self.assertNotIn("通用电影概念设计风格", user)
                self.assertNotIn("无特殊风格要求", user)

    def test_cover_image_prompt_includes_style_when_set(self):
        messages = self.builder.build_cover_image_prompt_messages(
            project_name="测试项目",
            aspect_ratio="16:9",
            outline_content="大纲",
            character_info="角色",
            visual_style="赛博朋克",
        )
        user = messages[-1]["content"]
        self.assertIn("【视觉风格】赛博朋克", user)
        self.assertIn("【画面风格要求】", user)
        self.assertIn("整体画面采用【赛博朋克】风格", user)

    def test_cover_image_prompt_omits_style_when_default_or_empty(self):
        for style in ("", "默认", "  ", None):
            with self.subTest(visual_style=style):
                messages = self.builder.build_cover_image_prompt_messages(
                    project_name="测试项目",
                    aspect_ratio="16:9",
                    outline_content="大纲",
                    character_info="角色",
                    visual_style=style or "",
                )
                user = messages[-1]["content"]
                self.assertNotIn("【视觉风格】", user)
                self.assertNotIn("【画面风格要求】", user)
                self.assertNotIn("通用电影海报风格", user)
                self.assertNotIn("无特殊风格要求", user)


if __name__ == "__main__":
    unittest.main()
