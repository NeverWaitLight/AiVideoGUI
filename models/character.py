from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Character:
    """角色数据模型"""
    id: int                      # 主键ID
    uuid: str                    # UUID（用于跨表关联）
    project_id: int              # 所属项目ID
    name: str                    # 角色名称
    ref_code: str                # 引用代号（如 CHAR_A、CHAR_B）
    design_image: str = ""       # 角色设计图路径
    description: str = ""        # 形象描述（结构化格式）
    voice_tone: str = ""         # 音色描述文字
    voice_reference_file: str = "" # 音色参考音频文件本地相对路径
    created_at: int = 0          # 创建时间（毫秒时间戳）
    updated_at: int = 0          # 更新时间（毫秒时间戳）


@dataclass
class CharacterHistory:
    """角色编辑历史数据模型"""
    id: int                      # 主键ID
    character_id: str            # 原始角色UUID
    project_id: int              # 所属项目ID
    name: str                    # 角色名称
    ref_code: str                # 引用代号
    design_image: str = ""       # 角色设计图路径
    description: str = ""        # 形象描述
    voice_tone: str = ""         # 音色描述文字
    voice_reference_file: str = "" # 音色参考音频文件本地相对路径
    created_at: int = 0          # 创建时间（毫秒时间戳）
