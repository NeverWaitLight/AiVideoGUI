import json
from typing import Any

from loguru import logger

from models.enums import SceneLocation, SceneTime


class ScriptParser:
    LOCATION_TYPE_MAP = {
        "interior": SceneLocation.INTERIOR,
        "exterior": SceneLocation.EXTERIOR,
        "interior_exterior": SceneLocation.INTERIOR_EXTERIOR,
    }

    TIME_TYPE_MAP = {
        "day": SceneTime.DAY,
        "night": SceneTime.NIGHT,
        "dawn": SceneTime.DAWN,
        "dusk": SceneTime.DUSK,
        "evening": SceneTime.EVENING,
        "custom": SceneTime.CUSTOM,
    }

    @classmethod
    def parse(cls, script_json: str) -> tuple[str, list[dict[str, Any]]]:
        """解析 JSON 格式的剧本"""
        script_json = script_json.strip()
        if script_json.startswith("```json"):
            script_json = script_json[7:]
        if script_json.startswith("```"):
            script_json = script_json[3:]
        if script_json.endswith("```"):
            script_json = script_json[:-3]
        script_json = script_json.strip()

        try:
            decoder = json.JSONDecoder(strict=False)
            data = decoder.decode(script_json)
        except json.JSONDecodeError as e:
            logger.error(f"剧本 JSON 解析失败: {e}")
            raise ValueError(f"无效的 JSON 格式: {e}")

        title = data.get("title", "")
        scenes_raw = data.get("scenes", [])
        scenes = []

        for scene in scenes_raw:
            scenes.append(cls.parse_scene_item(scene))

        logger.info(f"解析剧本完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes

    @classmethod
    def parse_scene_item(cls, scene: dict[str, Any]) -> dict[str, Any]:
        location_type = cls.LOCATION_TYPE_MAP.get(
            scene.get("location_type", "interior"),
            SceneLocation.INTERIOR,
        ).value

        time_type = cls.TIME_TYPE_MAP.get(
            scene.get("time_type", "day"),
            SceneTime.DAY,
        ).value

        return {
            "scene_number": scene.get("scene_number", 0),
            "location_type": location_type,
            "location": scene.get("location", ""),
            "time_type": time_type,
            "time_detail": scene.get("time_detail", ""),
            "content": scene.get("content", ""),
        }
