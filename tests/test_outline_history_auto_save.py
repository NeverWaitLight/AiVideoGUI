"""测试 Outline 历史版本自动保存功能。"""

import os
import tempfile
import unittest
import uuid
from datetime import datetime

from models.data_models import Outline, Project
from storage.database import DatabaseManager


class TestOutlineHistoryAutoSave(unittest.TestCase):
    """测试 Outline 更新时自动保存历史版本。"""

    def setUp(self):
        """创建临时数据库。"""
        # 每个测试使用独立的临时文件
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # 重置 SQLAlchemy 全局状态
        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        self.db = DatabaseManager(self.temp_db_path)

    def tearDown(self):
        """删除临时数据库。"""
        # 关闭所有数据库连接
        from storage.orm.base import close_session, engine
        close_session()
        if engine:
            engine.dispose()

        # 删除临时文件
        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass  # Windows 文件锁定，忽略

    def test_auto_save_history_on_update(self):
        """测试更新 Outline 时自动保存历史版本。"""
        # 1. 创建项目
        project_id = str(uuid.uuid4())
        self.db.create_project(
            project_id=project_id,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
        )

        # 2. 创建大纲
        outline_id = str(uuid.uuid4())
        outline = Outline(
            id=outline_id,
            project_id=project_id,
            content="初始大纲内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.create_outline(outline)

        # 3. 第一次更新大纲
        self.db.update_outline(outline_id, "第一次修改的内容")

        # 4. 验证历史版本已自动保存
        history_list = self.db.list_outline_history(outline_id)
        self.assertEqual(len(history_list), 1, "应该自动保存了 1 条历史记录")
        self.assertEqual(history_list[0].content, "第一次修改的内容")
        self.assertEqual(history_list[0].raw_id, outline_id)
        self.assertEqual(history_list[0].project_id, project_id)

        # 5. 第二次更新大纲
        self.db.update_outline(outline_id, "第二次修改的内容")

        # 6. 验证历史版本累积
        history_list = self.db.list_outline_history(outline_id)
        self.assertEqual(len(history_list), 2, "应该累积保存了 2 条历史记录")
        # 按时间倒序，最新的在前
        self.assertEqual(history_list[0].content, "第二次修改的内容")
        self.assertEqual(history_list[1].content, "第一次修改的内容")

    def test_history_contains_project_id(self):
        """测试历史记录包含 project_id 字段。"""
        # 1. 创建项目和大纲
        project_id = str(uuid.uuid4())
        self.db.create_project(
            project_id=project_id,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
        )

        outline_id = str(uuid.uuid4())
        outline = Outline(
            id=outline_id,
            project_id=project_id,
            content="初始内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.create_outline(outline)

        # 2. 更新大纲
        self.db.update_outline(outline_id, "新内容")

        # 3. 验证历史记录的 project_id
        history_list = self.db.list_outline_history(outline_id)
        self.assertEqual(len(history_list), 1, f"应该只有1条历史记录，实际有 {len(history_list)} 条")
        self.assertEqual(history_list[0].project_id, project_id, "历史记录应包含 project_id")


if __name__ == "__main__":
    unittest.main()
