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

    def list_characters(self, project_id: int) -> list[Character]:
        """获取项目的所有角色。"""
        return self._db.list_characters(project_id)

    def get_character(self, character_uuid: str) -> Character | None:
        """获取单个角色。"""
        return self._db.get_character(character_uuid)

    def create_character(
        self,
        project_id: int,
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

    def get_by_ref_code(self, project_id: int, ref_code: str) -> Character | None:
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

    # 固定特征标签——跨视频保持一致，不随场景变化
    _FIXED_TAGS = ("外貌", "发型", "发色", "瞳色", "体型")

    @classmethod
    def extract_fixed_traits(cls, description: str) -> str:
        """从结构化描述中提取固定特征部分。

        解析形如 ``[外貌] ...\\n[发型] ...`` 的结构化文本，
        只返回固定特征标签对应的内容。若描述未使用结构化格式，
        则回退返回原始文本（兼容旧数据）。
        """
        if not description:
            return ""

        parts: list[str] = []
        has_structured_tags = False

        # 所有已知标签（固定 + 服装）
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

        # 结构化格式但没有固定特征 → 返回空；非结构化描述 → 回退返回原文
        return "" if has_structured_tags else description

    def enrich_prompt_with_characters(
        self, visual_content: str, project_id: int
    ) -> str:
        """将角色的固定外貌特征拼接到视频生成提示词中。

        扫描 visual_content 中出现的角色 name 或 ref_code，
        仅注入固定特征（发型、发色、瞳色、体型等），
        服装信息由分镜画面描述自行提供，避免冲突。
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

        prefix_lines = []
        for c in matched:
            traits = self.extract_fixed_traits(c.description)
            if traits:
                prefix_lines.append(f"[角色形象] {c.ref_code}：{traits}")

        if not prefix_lines:
            return visual_content

        return "\n".join(prefix_lines) + f"\n[画面] {visual_content}"
