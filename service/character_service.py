import time
import uuid

from loguru import logger

from models.character import Character, CharacterHistory
from storage.session_manager import SessionManager
from storage.repositories.character_repository import CharacterRepository, CharacterHistoryRepository
from utils.path_converter import to_relative_path

class CharacterService:

    def __init__(self, session_manager: SessionManager, workspace_root: str) -> None:
        self._sm = session_manager
        self._workspace_root = workspace_root

    def list_characters(self, project_id: int) -> list[Character]:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        return character_repo.list_by_project(project_id)

    def get_character(self, character_uuid: str) -> Character | None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        return character_repo.get_by_id(character_uuid)

    def create_character(
        self,
        project_id: int,
        name: str,
        ref_code: str,
        description: str = "",
        design_image: str = "",
    ) -> Character:
        relative_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        character = Character(
            id=0,
            uuid=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            ref_code=ref_code,
            description=description,
            design_image=relative_design_image,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000),
        )

        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        self._sm.begin_write()
        try:
            created = character_repo.save(character=character)
            self._sm.commit_write()
            logger.info(f"创建角色：name={name}, ref_code={ref_code}")
            return created
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建角色失败：{e}")
            raise

    def update_character(
        self,
        character_uuid: str,
        name: str | None = None,
        ref_code: str | None = None,
        description: str | None = None,
        design_image: str | None = None,
    ) -> None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)

        character = character_repo.get_by_id(character_uuid)
        if not character:
            logger.warning(f"角色不存在：{character_uuid}")
            return

        final_design_image = character.design_image
        if design_image is not None:
            final_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        updated_character = Character(
            id=character.id,
            uuid=character.uuid,
            project_id=character.project_id,
            name=name if name is not None else character.name,
            ref_code=ref_code if ref_code is not None else character.ref_code,
            description=description if description is not None else character.description,
            design_image=final_design_image,
            created_at=character.created_at,
            updated_at=int(time.time() * 1000),
        )

        self._sm.begin_write()
        try:
            character_repo.update(dto=updated_character)
            self._sm.commit_write()
            logger.info(f"更新角色：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新角色失败：{e}")
            raise

    def delete_character(self, character_uuid: str) -> None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)

        self._sm.begin_write()
        try:
            character_repo.delete(character_uuid=character_uuid)
            self._sm.commit_write()
            logger.info(f"删除角色：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除角色失败：{e}")
            raise

    def batch_create_characters(self, characters: list[Character]) -> None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)

        self._sm.begin_write()
        try:
            character_repo.batch_create(characters=characters)
            self._sm.commit_write()
            logger.info(f"批量创建 {len(characters)} 个角色")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"批量创建角色失败：{e}")
            raise

    def get_by_ref_code(self, project_id: int, ref_code: str) -> Character | None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        return character_repo.get_by_ref_code(project_id=project_id, ref_code=ref_code)

    def save_history(self, character_uuid: str) -> None:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        history_repo = self._sm.get_repo(repo_class=CharacterHistoryRepository)

        character = character_repo.get_by_id(character_uuid)
        if not character:
            logger.warning(f"角色不存在：{character_uuid}")
            return

        history = CharacterHistory(
            id=0,
            character_id=character.uuid,
            project_id=character.project_id,
            name=character.name,
            ref_code=character.ref_code,
            design_image=character.design_image,
            description=character.description,
            created_at=int(time.time() * 1000),
        )

        self._sm.begin_write()
        try:
            history_repo.save(history=history)
            self._sm.commit_write()
            logger.info(f"保存角色历史：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"保存角色历史失败：{e}")
            raise

    def list_history(self, character_uuid: str) -> list[CharacterHistory]:
        history_repo = self._sm.get_repo(repo_class=CharacterHistoryRepository)
        return history_repo.list_by_character(character_uuid)

    _FIXED_TAGS = ("物种", "外貌", "发型", "发色", "瞳色", "体型")

    @classmethod
    def extract_fixed_traits(cls, description: str) -> str:
        if not description:
            return ""

        parts: list[str] = []
        has_structured_tags = False

        _all_tags = cls._FIXED_TAGS + ("上装", "裤子", "鞋袜", "帽子")

        for line in description.splitlines():
            stripped = line.strip()
            for tag in _all_tags:
                if stripped.startswith(f"[{tag}]"):
                    has_structured_tags = True
                    if tag in cls._FIXED_TAGS:
                        value = stripped[len(f"[{tag}]"):].strip()
                        if value:
                            parts.append(value)
                    break

        if parts:
            return "，".join(parts)

        return "" if has_structured_tags else description

    def enrich_prompt_with_characters(
        self, visual_content: str, project_id: int
    ) -> str:
        character_repo = self._sm.get_repo(repo_class=CharacterRepository)
        characters = character_repo.list_by_project(project_id)
        if not characters:
            return visual_content

        matched = []
        for char in characters:
            if char.ref_code in visual_content or char.name in visual_content:
                if char.description:
                    matched.append(char)

        if not matched:
            return visual_content

        replaced_content = visual_content
        for c in sorted(matched, key=lambda ch: len(ch.name), reverse=True):
            if c.name and c.name in replaced_content:
                replaced_content = replaced_content.replace(c.name, c.ref_code)

        prefix_lines = []
        for c in matched:
            traits = self.extract_fixed_traits(c.description)
            if traits:
                traits_clean = self._clean_format_markers(traits)
                prefix_lines.append(f"[角色形象] {c.ref_code}：{traits_clean}")

        if not prefix_lines:
            return replaced_content

        return "\n".join(prefix_lines) + f"\n[画面] {replaced_content}"

    @staticmethod
    def _clean_format_markers(text: str) -> str:
        import re

        if not text:
            return text

        text = re.sub(r'<br\s*/?>', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)

        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_([^_]+?)_', r'\1', text)

        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text
