"""角色服务层：管理角色 CRUD 和编辑历史。"""

from loguru import logger
import uuid
from datetime import datetime

from models.character import Character, CharacterHistory
from storage.session_manager import SessionManager
from storage.repositories.character_repository import CharacterRepository, CharacterHistoryRepository
from utils.path_converter import to_relative_path

class CharacterService:
    """角色业务逻辑服务。"""

    def __init__(self, session_manager: SessionManager, workspace_root: str) -> None:
        self._sm = session_manager
        self._workspace_root = workspace_root

    def list_characters(self, project_id: int) -> list[Character]:
        """获取项目的所有角色。"""
        character_repo = self._sm.get_repo(CharacterRepository)
        return character_repo.list_by_project(project_id)

    def get_character(self, character_uuid: str) -> Character | None:
        """获取单个角色。"""
        character_repo = self._sm.get_repo(CharacterRepository)
        return character_repo.get_by_id(character_uuid)

    def create_character(
        self,
        project_id: int,
        name: str,
        ref_code: str,
        description: str = "",
        design_image: str = "",
    ) -> Character:
        """创建新角色。"""
        # 转换为相对路径存储
        relative_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        character = Character(
            id=0,
            uuid=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            ref_code=ref_code,
            description=description,
            design_image=relative_design_image,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        character_repo = self._sm.get_repo(CharacterRepository)
        self._sm.begin_write()
        try:
            created = character_repo.save(character)
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
        """更新角色信息（ORM 监听器自动保存历史快照）。"""
        character_repo = self._sm.get_repo(CharacterRepository)

        # 先读取现有角色
        character = character_repo.get_by_id(character_uuid)
        if not character:
            logger.warning(f"角色不存在：{character_uuid}")
            return

        # 转换设计图路径为相对路径（如果提供了新路径）
        final_design_image = character.design_image
        if design_image is not None:
            final_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        # 更新字段
        updated_character = Character(
            id=character.id,
            uuid=character.uuid,
            project_id=character.project_id,
            name=name if name is not None else character.name,
            ref_code=ref_code if ref_code is not None else character.ref_code,
            description=description if description is not None else character.description,
            design_image=final_design_image,
            created_at=character.created_at,
            updated_at=datetime.now(),
        )

        self._sm.begin_write()
        try:
            character_repo.update(updated_character)
            self._sm.commit_write()
            logger.info(f"更新角色：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新角色失败：{e}")
            raise

    def delete_character(self, character_uuid: str) -> None:
        """删除角色。"""
        character_repo = self._sm.get_repo(CharacterRepository)

        self._sm.begin_write()
        try:
            character_repo.delete(character_uuid)
            self._sm.commit_write()
            logger.info(f"删除角色：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除角色失败：{e}")
            raise

    def batch_create_characters(self, characters: list[Character]) -> None:
        """批量创建角色（AI 提取后用）。"""
        character_repo = self._sm.get_repo(CharacterRepository)

        self._sm.begin_write()
        try:
            character_repo.batch_create(characters)
            self._sm.commit_write()
            logger.info(f"批量创建 {len(characters)} 个角色")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"批量创建角色失败：{e}")
            raise

    def get_by_ref_code(self, project_id: int, ref_code: str) -> Character | None:
        """根据引用代号查找角色。"""
        character_repo = self._sm.get_repo(CharacterRepository)
        return character_repo.get_by_ref_code(project_id, ref_code)

    def save_history(self, character_uuid: str) -> None:
        """手动保存角色当前状态到历史。"""
        character_repo = self._sm.get_repo(CharacterRepository)
        history_repo = self._sm.get_repo(CharacterHistoryRepository)

        # 先读取角色
        character = character_repo.get_by_id(character_uuid)
        if not character:
            logger.warning(f"角色不存在：{character_uuid}")
            return

        # 创建历史记录
        history = CharacterHistory(
            id=0,  # 自增ID
            character_id=character.uuid,
            project_id=character.project_id,
            name=character.name,
            ref_code=character.ref_code,
            design_image=character.design_image,
            description=character.description,
            created_at=datetime.now(),
        )

        self._sm.begin_write()
        try:
            history_repo.save(history)
            self._sm.commit_write()
            logger.info(f"保存角色历史：uuid={character_uuid}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"保存角色历史失败：{e}")
            raise

    def list_history(self, character_uuid: str) -> list[CharacterHistory]:
        """获取角色的编辑历史。"""
        history_repo = self._sm.get_repo(CharacterHistoryRepository)
        return history_repo.list_by_character(character_uuid)

    # 固定特征标签——跨视频保持一致，不随场景变化
    _FIXED_TAGS = ("物种", "外貌", "发型", "发色", "瞳色", "体型")

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
        仅注入固定特征（物种、外貌、发型、发色、瞳色、体型等），
        服装信息由分镜画面描述自行提供，避免冲突。

        同时将画面描述中的角色名替换为 ref_code，使视频生成模型
        能够将角色形象描述与画面中的动作明确关联。

        自动清理描述中的 HTML 标签和 Markdown 格式控制符，
        确保最终提示词为纯文本。
        """
        character_repo = self._sm.get_repo(CharacterRepository)
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

        # 将画面描述中的角色名替换为 ref_code
        # 按名字长度降序排列，防止短名是长名子串时产生误替换
        replaced_content = visual_content
        for c in sorted(matched, key=lambda ch: len(ch.name), reverse=True):
            if c.name and c.name in replaced_content:
                replaced_content = replaced_content.replace(c.name, c.ref_code)

        prefix_lines = []
        for c in matched:
            traits = self.extract_fixed_traits(c.description)
            if traits:
                # 清理格式控制符
                traits_clean = self._clean_format_markers(traits)
                prefix_lines.append(f"[角色形象] {c.ref_code}：{traits_clean}")

        if not prefix_lines:
            return replaced_content

        return "\n".join(prefix_lines) + f"\n[画面] {replaced_content}"

    @staticmethod
    def _clean_format_markers(text: str) -> str:
        """清理文本中的 HTML 标签和 Markdown 格式控制符。

        移除常见的格式控制符，确保提示词为纯文本：
        - HTML 标签：<br>, <b>, <i>, <strong>, <em> 等
        - Markdown 粗体/斜体：**text**, *text*, __text__, _text_
        - Markdown 标题标记：# ## ###
        """
        import re

        if not text:
            return text

        # 移除 HTML 标签（包括自闭合标签），替换为空格以保持词语间距
        text = re.sub(r'<br\s*/?>', ' ', text)  # <br> 和 <br/> 替换为空格
        text = re.sub(r'<[^>]+>', '', text)     # 其他标签直接移除

        # 移除 Markdown 粗体和斜体（避免误删除普通星号和下划线）
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # *italic*
        text = re.sub(r'_([^_]+?)_', r'\1', text)     # _italic_

        # 移除 Markdown 标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # 清理多余空白字符（多个空格/换行符合并为单个空格）
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text
