from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Character:
    """角色数据结构"""
    id: int  # 自增ID
    uuid: str  # UUID标识
    project_id: int  # 所属项目ID
    name: str  # 角色名
    ref_code: str  # 引用代号（如 CHAR_A）
    design_image: str = ""  # 角色设计图路径（可为空）
    description: str = ""  # 形象描述
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CharacterHistory:
    """角色编辑历史（逐条快照，字段与 Character 一致）"""
    id: int  # 自增ID
    character_id: str  # 关联角色的UUID
    project_id: int  # 所属项目ID
    name: str  # 角色名
    ref_code: str  # 引用代号
    design_image: str = ""  # 角色设计图路径
    description: str = ""  # 形象描述
    created_at: int = 0  # 13位时间戳（毫秒）
