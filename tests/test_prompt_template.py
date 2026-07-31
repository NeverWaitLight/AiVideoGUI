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
        self.assertIn("chat", templates)
        self.assertIn("outline_optimization", templates)
        self.assertIn("image_prompt_generation", templates)

    def test_get_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("chat")
        self.assertIsInstance(template, PromptTemplate)
        self.assertIn("助手", template.system_prompt)

    def test_get_nonexistent_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        with self.assertRaises(KeyError):
            manager.get_template("nonexistent_template")

    def test_chat_template_build(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("chat")
        messages = template.build_messages(user_input="你好")

        self.assertGreater(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"].strip(), "你好")

    def test_outline_optimization_template(self):
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("outline_optimization")
        messages = template.build_messages(
            original_content="这是原始大纲",
            user_requirement="增加悬疑元素",
        )

        self.assertGreater(len(messages), 0)
        last_message = messages[-1]["content"]
        self.assertIn("这是原始大纲", last_message)
        self.assertIn("增加悬疑元素", last_message)


if __name__ == "__main__":
    unittest.main()
