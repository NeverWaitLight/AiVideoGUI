"""测试工作区路径工具函数。"""

import os
import unittest

from utils import paths


class TestPaths(unittest.TestCase):
    """测试路径解析函数。"""

    def test_data_dir(self):
        result = paths.data_dir("/app")
        self.assertEqual(result, os.path.join("/app", "data"))

    def test_cache_dir(self):
        result = paths.cache_dir("/app")
        self.assertEqual(result, os.path.join("/app", "cache"))

    def test_logs_dir(self):
        result = paths.logs_dir("/app")
        self.assertEqual(result, os.path.join("/app", "logs"))

    def test_workspace_dir(self):
        result = paths.workspace_dir("/app")
        self.assertEqual(result, os.path.join("/app", "workspace"))

    def test_chat_dir(self):
        result = paths.chat_dir("/app")
        self.assertEqual(result, os.path.join("/app", "workspace", "chat"))

    def test_projects_dir(self):
        result = paths.projects_dir("/app")
        self.assertEqual(result, os.path.join("/app", "workspace", "projects"))

    def test_project_dir(self):
        result = paths.project_dir("/app", 12345)
        self.assertEqual(result, os.path.join("/app", "workspace", "projects", "12345"))

    def test_thumbnail_dir(self):
        result = paths.thumbnail_dir("/app/workspace/chat")
        self.assertEqual(result, os.path.join("/app/workspace/chat", ".thumbnails"))


if __name__ == "__main__":
    unittest.main()
