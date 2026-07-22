"""角色服务层：管理角色 CRUD 和编辑历史。"""

import logging
import uuid
from datetime import datetime

from models.data_models import Character, CharacterHistory
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class CharacterService:
    """角色业务逻辑服务。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def list_characters(self, project_id: str) -> list[Character]:
        """获取项目的所有角色。"""
        return self._db.list_characters(project_id)

    def get_character(self, character_uuid: str) -> Character | None:
        """获取单个角色。"""
        return self._db.get_character(character_uuid)

    def create_character(
        self,
        project_id: str,
        name: str,
        ref_code: str,
        description: str = "",
        design_image: str = "",
    ) -> Character:
        """创建新角色。"""
        character = Character(
            id=0,
            uuid=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            ref_code=ref_code,
            description=description,
            design_image=design_image,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        result = self._db.create_character(character)
        logger.info(f"创建角色：name={name}, ref_code={ref_code}")
        return result

    def update_character(
        self,
        character_uuid: str,
        name: str | None = None,
        ref_code: str | None = None,
        description: str | None = None,
        design_image: str | None = None,
    ) -> None:
        """更新角色信息（更新前保存历史快照）。"""
        character = self._db.get_character(character_uuid)
        if not character:
            logger.warning(f"角色不存在：{character_uuid}")
            return

        # 保存历史快照
        self._db.create_character_history(character)

        # 更新字段
        if name is not None:
            character.name = name
        if ref_code is not None:
            character.ref_code = ref_code
        if description is not None:
            character.description = description
        if design_image is not None:
            character.design_image = design_image
        character.updated_at = datetime.now()

        self._db.update_character(character)
        logger.info(f"更新角色：uuid={character_uuid}")

    def delete_character(self, character_uuid: str) -> None:
        """删除角色。"""
        self._db.delete_character(character_uuid)
        logger.info(f"删除角色：uuid={character_uuid}")

    def batch_create_characters(self, characters: list[Character]) -> None:
        """批量创建角色（AI 提取后用）。"""
        self._db.batch_create_characters(characters)
        logger.info(f"批量创建 {len(characters)} 个角色")

    def get_by_ref_code(self, project_id: str, ref_code: str) -> Character | None:
        """根据引用代号查找角色。"""
        return self._db.get_character_by_ref_code(project_id, ref_code)

    def save_history(self, character_uuid: str) -> None:
        """手动保存角色当前状态到历史。"""
        character = self._db.get_character(character_uuid)
        if character:
            self._db.create_character_history(character)
            logger.info(f"保存角色历史：uuid={character_uuid}")

    def list_history(self, character_uuid: str) -> list[CharacterHistory]:
        """获取角色的编辑历史。"""
        return self._db.list_character_history(character_uuid)

    def enrich_prompt_with_characters(
        self, visual_content: str, project_id: str
    ) -> str:
        """将角色形象描述拼接到视频生成提示词中。

        扫描 visual_content 中出现的角色 name 或 ref_code，
        将匹配角色的形象描述作为前缀拼接。
        """
        characters = self._db.list_characters(project_id)
        if not characters:
            return visual_content

        matched = []
        for char in characters:
            if char.ref_code in visual_content or char.name in visual_content:
                if char.description:
                    matched.append(char)

        if not matched:
            return visual_content

        prefix_lines = [
            f"[角色形象] {c.ref_code}：{c.description}" for c in matched
        ]
        return "\n".join(prefix_lines) + f"\n[画面] {visual_content}"
