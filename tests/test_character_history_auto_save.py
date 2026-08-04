import os
import tempfile
import unittest
import uuid
from datetime import datetime

from models.character import Character
from models.project import Project
from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.character_repository import CharacterRepository, CharacterHistoryRepository


class TestCharacterHistoryAutoSave(unittest.TestCase):

    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        database_url = f"sqlite:///{self.temp_db_path}"
        init_engine(database_url, echo=False)
        create_all_tables()

    def tearDown(self):
        from storage.orm.base import engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_character(self, name="主角A", ref_code="CHAR_A",
                                       description="高个子男性", design_image=""):
        session = get_session()
        project_repo = ProjectRepository(session)
        character_repo = CharacterRepository(session)

        now = datetime.now()
        now_ms = int(now.timestamp() * 1000)

        project = Project(
            id=0,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
            created_at=now_ms,
            updated_at=now_ms,
            cover_image="",
        )
        project = project_repo.create(project)
        session.commit()

        character = Character(
            id=0,
            uuid=str(uuid.uuid4()),
            project_id=project.id,
            name=name,
            ref_code=ref_code,
            design_image=design_image,
            description=description,
            created_at=now_ms,
            updated_at=now_ms,
        )
        character_repo.create(character)
        session.commit()

        character = character_repo.get_by_id(character.uuid)

        return project, character

    def test_auto_save_history_on_insert(self):
        project, character = self._create_project_and_character()

        session = get_session()
        history_repo = CharacterHistoryRepository(session)
        history = history_repo.list_by_character(character.uuid)

        self.assertEqual(len(history), 1, "创建角色后应自动保存 1 条历史")
        self.assertEqual(history[0].name, "主角A")
        self.assertEqual(history[0].ref_code, "CHAR_A")
        self.assertEqual(history[0].description, "高个子男性")

    def test_auto_save_history_on_update(self):
        project, character = self._create_project_and_character()

        session = get_session()
        character_repo = CharacterRepository(session)
        history_repo = CharacterHistoryRepository(session)

        character.name = "主角A改名"
        character.description = "矮个子男性"
        character_repo.update(character)
        session.commit()

        history = history_repo.list_by_character(character.uuid)
        self.assertEqual(len(history), 2, "创建+更新后应有 2 条历史")
        self.assertEqual(history[0].name, "主角A改名")
        self.assertEqual(history[0].description, "矮个子男性")

    def test_no_history_on_updated_at_only(self):
        project, character = self._create_project_and_character()

        session = get_session()
        character_repo = CharacterRepository(session)
        history_repo = CharacterHistoryRepository(session)

        character_repo.update(character)
        session.commit()

        history = history_repo.list_by_character(character.uuid)
        self.assertEqual(len(history), 1, "关键字段未变时不应新增历史")

    def test_multiple_updates_accumulate(self):
        project, character = self._create_project_and_character()

        session = get_session()
        character_repo = CharacterRepository(session)
        history_repo = CharacterHistoryRepository(session)

        character.name = "版本2"
        character_repo.update(character)
        session.commit()

        character.name = "版本3"
        character_repo.update(character)
        session.commit()

        history = history_repo.list_by_character(character.uuid)
        self.assertEqual(len(history), 3, "创建+2次更新应有 3 条历史")

    def test_history_snapshot_fields(self):
        project, character = self._create_project_and_character(
            name="角色X", ref_code="CHAR_X",
            description="详细描述", design_image="img.png",
        )

        session = get_session()
        history_repo = CharacterHistoryRepository(session)
        history = history_repo.list_by_character(character.uuid)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].name, "角色X")
        self.assertEqual(history[0].ref_code, "CHAR_X")
        self.assertEqual(history[0].description, "详细描述")
        self.assertEqual(history[0].design_image, "img.png")
        self.assertEqual(history[0].character_id, character.uuid)
        self.assertEqual(history[0].project_id, project.id)


if __name__ == "__main__":
    unittest.main()
