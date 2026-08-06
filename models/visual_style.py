from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisualStyle:
    """视觉风格数据模型"""
    id: int                     # 主键ID
    name: str                   # 风格名称
    is_default: bool            # 是否为默认风格
    sample_image_path: str      # 样例图片路径
    created_at: int             # 创建时间（毫秒时间戳）
    updated_at: int             # 更新时间（毫秒时间戳）
