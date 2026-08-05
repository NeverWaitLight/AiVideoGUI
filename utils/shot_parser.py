"""分镜数据解析器"""

import json
from loguru import logger
from typing import Any

from models.enums import ShotSize


class ShotParser:
    SHOT_SIZE_MAP = {
        "extreme_close_up": ShotSize.EXTREME_CLOSE_UP,
        "close_up": ShotSize.CLOSE_UP,
        "medium_shot": ShotSize.MEDIUM_SHOT,
        "full_shot": ShotSize.FULL_SHOT,
        "long_shot": ShotSize.LONG_SHOT,
        "extreme_long_shot": ShotSize.EXTREME_LONG_SHOT,
    }

    @classmethod
    def parse(cls, storyboard_json: str) -> list[dict[str, Any]]:
        """解析 JSON 格式的分镜数据

        Returns:
            分镜列表
        """
        # 清洗 Markdown 代码块标记
        storyboard_json = storyboard_json.strip()
        if storyboard_json.startswith("```json"):
            storyboard_json = storyboard_json[7:]
        if storyboard_json.startswith("```"):
            storyboard_json = storyboard_json[3:]
        if storyboard_json.endswith("```"):
            storyboard_json = storyboard_json[:-3]
        storyboard_json = storyboard_json.strip()

        try:
            # strict=False 允许字符串值中包含未转义的控制字符（如换行符），
            # 部分 LLM 会在 JSON 字符串中输出真实换行符而非 \n 转义序列
            decoder = json.JSONDecoder(strict=False)
            data = decoder.decode(storyboard_json)
        except json.JSONDecodeError as e:
            logger.error(f"分镜 JSON 解析失败: {e}")
            logger.error(f"原始文本:\n{storyboard_json[:500]}")
            raise ValueError(f"无效的 JSON 格式: {e}")

        shots = cls._parse_shots(data.get("storyboard", []))

        logger.info(f"解析分镜完成：共 {len(shots)} 个镜头")
        return shots

    @classmethod
    def _parse_shots(cls, shots_raw: list[dict]) -> list[dict[str, Any]]:
        shots = []
        for shot in shots_raw:
            shot_size_str = shot.get("shot_size", "medium_shot")
            shot_size_enum = cls.SHOT_SIZE_MAP.get(shot_size_str, ShotSize.MEDIUM_SHOT)
            if shot_size_str not in cls.SHOT_SIZE_MAP:
                logger.warning(f"未识别的景别值 '{shot_size_str}'，使用默认值 medium_shot")

            shots.append({
                "scene_number": shot.get("scene_number", 0),
                "shot_number": shot.get("shot_number", 0),
                "shot_size": shot_size_enum.value,
                "camera_movement": shot.get("camera_movement", ""),
                "visual_content": shot.get("visual_content", ""),
                "dialogue": shot.get("dialogue", ""),
                "sound_effect": shot.get("sound_effect", ""),
                "duration": float(shot.get("duration", 0.0)),
                "notes": shot.get("notes", ""),
            })
        return shots
