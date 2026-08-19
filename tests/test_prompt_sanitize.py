import json
import unittest
from unittest.mock import Mock, patch

from models.provider_config import ProviderConfig
from service.chat_service import ChatService
from service.image_service import ImageService
from service.video_service import VideoService
from utils.prompt_sanitize import flatten_prompt_text, sanitize_chat_messages


class TestPromptSanitizeUtils(unittest.TestCase):
    def test_flatten_prompt_text_removes_newlines_and_indent(self):
        text = "  第一行\n\t第二行\r\n  第三行  "
        self.assertEqual(flatten_prompt_text(text), "第一行 第二行 第三行")

    def test_flatten_prompt_text_removes_control_chars(self):
        text = "hello\x00world\x1f!"
        self.assertEqual(flatten_prompt_text(text), "hello world !")

    def test_flatten_prompt_text_empty(self):
        self.assertEqual(flatten_prompt_text(""), "")

    def test_sanitize_chat_messages_only_string_content(self):
        messages = [
            {"role": "system", "content": "系统\n提示"},
            {"role": "user", "content": [{"text": "多模态"}]},
            {"role": "assistant", "content": "  回答\r\n内容  "},
        ]
        sanitized = sanitize_chat_messages(messages)

        self.assertEqual(sanitized[0]["content"], "系统 提示")
        self.assertEqual(sanitized[1]["content"], [{"text": "多模态"}])
        self.assertEqual(sanitized[2]["content"], "回答 内容")


class TestChatServicePromptSanitize(unittest.TestCase):
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.settings.default_chat_provider = "dashscope"
        self.config_manager.resolve_config_for_type.return_value = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            default_model="qwen-max",
        )

        self.session_manager = Mock()
        self.prompt_builder = Mock()

        self.chat_service = ChatService(
            config_manager=self.config_manager,
            session_manager=self.session_manager,
            text_prompt_builder=self.prompt_builder,
        )

    def test_call_provider_sanitizes_messages_before_chat(self):
        provider = Mock()
        provider.chat.return_value = "ok"
        self.chat_service._providers["dashscope"] = provider

        messages = [
            {"role": "system", "content": "你是\n助手"},
            {"role": "user", "content": "  请回答\t问题  "},
        ]

        result = self.chat_service._call_provider(messages, "qwen-max")

        self.assertEqual(result, "ok")
        provider.chat.assert_called_once()
        sent_messages = provider.chat.call_args.kwargs["messages"]
        self.assertEqual(sent_messages[0]["content"], "你是 助手")
        self.assertEqual(sent_messages[1]["content"], "请回答 问题")


class TestVideoServicePromptSanitize(unittest.TestCase):
    def setUp(self):
        self.session_manager = Mock()
        self.task_repo = Mock()
        self.session_manager.get_repo.return_value = self.task_repo
        self.task_repo.add.return_value = 1

        self.config = Mock()
        self.config.get_provider_config.return_value = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            default_model="wan2.7-t2v-2026-06-12",
        )

        self.provider = Mock()
        self.provider._config = ProviderConfig(
            provider_name="dashscope",
            default_model="wan2.7-t2v-2026-06-12",
        )
        self.provider.t2v.return_value = ("task-1", {"json": {"input": {"prompt": "x"}}})

        self.video_service = VideoService(
            session_manager=self.session_manager,
            config=self.config,
            chat_service=Mock(),
        )
        self.video_service._providers["dashscope"] = self.provider

    def test_submit_task_flattens_prompt_before_t2v(self):
        prompt = "【镜头画面】\n小明推开门\n\t阳光洒进来"

        provider_task_id = self.video_service.submit_task(
            prompt=prompt,
            provider_name="dashscope",
        )

        self.assertEqual(provider_task_id, "task-1")
        submitted_prompt = self.provider.t2v.call_args.kwargs["prompt"]
        self.assertEqual(submitted_prompt, "【镜头画面】 小明推开门 阳光洒进来")
        self.assertNotIn("\n", submitted_prompt)
        self.assertNotIn("\t", submitted_prompt)


class TestImageServicePromptSanitize(unittest.TestCase):
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.resolve_config_for_type.return_value = ProviderConfig(
            provider_name="dashscope_image",
            api_key="test-key",
            default_model="wan2.6-t2i",
        )

        self.task_repo = Mock()
        self.session_manager = Mock()
        self.session_manager.get_repo.return_value = self.task_repo

        self.image_service = ImageService(
            config_manager=self.config_manager,
            session_manager=self.session_manager,
            chat_service=Mock(),
            prompt_builder=Mock(),
            storyboard_service=Mock(),
            character_service=Mock(),
            project_service=Mock(),
            workspace_root="/tmp/workspace",
        )

    @patch("service.image_service.uuid.uuid4", return_value="task-id-123")
    def test_generate_flattens_prompt_before_persist(self, _mock_uuid):
        prompt = "  角色立绘\n\t细节描述  "
        negative_prompt = "  低质量\n模糊  "

        provider_task_id = self.image_service.generate(
            prompt=prompt,
            local_path="images/test.png",
            negative_prompt=negative_prompt,
        )

        self.assertEqual(provider_task_id, "task-id-123")
        request_params = json.loads(self.task_repo.add.call_args.kwargs["request_params"])
        self.assertEqual(request_params["prompt"], "角色立绘 细节描述")
        self.assertEqual(request_params["negative_prompt"], "低质量 模糊")
        self.assertNotIn("\n", request_params["prompt"])
        self.assertNotIn("\n", request_params["negative_prompt"])


if __name__ == "__main__":
    unittest.main()
