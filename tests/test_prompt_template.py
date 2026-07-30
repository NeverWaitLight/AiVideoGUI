"""提示词模板管理器测试。"""

import unittest
from pathlib import Path
from prompts.manager import PromptTemplate, PromptTemplateManager


class TestPromptTemplate(unittest.TestCase):
    """测试 PromptTemplate 类。"""

    def test_build_messages_without_few_shot(self):
        """测试构建不含 few-shot 的消息。"""
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
        """测试构建含 few-shot 的消息。"""
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

        self.assertEqual(len(messages), 6)  # system + 2 few-shot pairs + user
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
    """测试 PromptTemplateManager 类。"""

    def test_load_templates(self):
        """测试加载模板文件。"""
        # 使用项目中的实际模板目录
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        # 验证模板已加载
        templates = manager.list_templates()
        self.assertGreater(len(templates), 0)
        self.assertIn("chat", templates)
        self.assertIn("outline_optimization", templates)
        self.assertIn("image_prompt_generation", templates)

    def test_get_template(self):
        """测试获取模板。"""
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        # 获取存在的模板
        template = manager.get_template("chat")
        self.assertIsInstance(template, PromptTemplate)
        self.assertIn("助手", template.system_prompt)

    def test_get_nonexistent_template(self):
        """测试获取不存在的模板。"""
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        # 尝试获取不存在的模板
        with self.assertRaises(KeyError):
            manager.get_template("nonexistent_template")

    def test_chat_template_build(self):
        """测试聊天模板构建消息。"""
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("chat")
        messages = template.build_messages(user_input="你好")

        # 验证消息结构
        self.assertGreater(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        # 模板可能包含换行符，使用 strip 比较
        self.assertEqual(messages[-1]["content"].strip(), "你好")

    def test_outline_optimization_template(self):
        """测试大纲优化模板。"""
        templates_dir = Path(__file__).parent.parent / "prompts" / "templates"
        manager = PromptTemplateManager(templates_dir)

        template = manager.get_template("outline_optimization")
        messages = template.build_messages(
            original_content="这是原始大纲",
            user_requirement="增加悬疑元素",
        )

        # 验证消息内容
        self.assertGreater(len(messages), 0)
        last_message = messages[-1]["content"]
        self.assertIn("这是原始大纲", last_message)
        self.assertIn("增加悬疑元素", last_message)


if __name__ == "__main__":
    unittest.main()
