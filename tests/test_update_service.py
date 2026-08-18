"""更新服务测试"""

import unittest
from unittest.mock import patch, MagicMock
from service.update_service import UpdateService


class TestUpdateService(unittest.TestCase):
    def setUp(self):
        self.service = UpdateService(
            current_version="0.0.1",
            workspace_root="C:/test",
            github_api_url="https://api.github.com/repos/NeverWaitLight/AiVideoGUI/releases/latest",
            github_repo="NeverWaitLight/AiVideoGUI",
        )

    @patch("service.update_service.requests.get")
    def test_check_update_new_version_available(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tag_name": "v0.2.0",
            "body": "新版本发布说明",
            "published_at": "2026-08-10T00:00:00Z",
            "html_url": "https://github.com/NeverWaitLight/AiVideoGUI/releases/tag/v0.2.0",
            "assets": [
                {
                    "name": "AI-Video-GUI-Setup.exe",
                    "browser_download_url": "https://github.com/NeverWaitLight/AiVideoGUI/releases/download/v0.2.0/AI-Video-GUI-Setup.exe"
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.service.check_update()

        self.assertIsNotNone(result)
        self.assertEqual(result["version"], "0.2.0")
        self.assertIn("AI-Video-GUI-Setup.exe", result["download_url"])
        self.assertEqual(result["release_notes"], "新版本发布说明")

    @patch("service.update_service.requests.get")
    def test_check_update_no_new_version(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tag_name": "v0.0.1",
            "body": "当前版本",
            "published_at": "2026-08-01T00:00:00Z",
            "html_url": "https://github.com/NeverWaitLight/AiVideoGUI/releases/tag/v0.0.1",
            "assets": []
        }
        mock_get.return_value = mock_response

        result = self.service.check_update()

        self.assertIsNone(result)

    @patch("service.update_service.requests.get")
    def test_check_update_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = self.service.check_update()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
