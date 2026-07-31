from loguru import logger
import re
from typing import Any

from models.enums import SceneLocation, SceneTime

class ScriptParser:
    SCENE_HEADER_PATTERN = re.compile(
        r"第\s*(\d+)\s*场\s+(内景|外景|内景/外景)\s+(.+?)\s*[-—]\s*(.+)",
        re.IGNORECASE,
    )

    LOCATION_TYPE_MAP = {
        "内景": SceneLocation.INTERIOR,
        "外景": SceneLocation.EXTERIOR,
        "内景/外景": SceneLocation.INTERIOR_EXTERIOR,
    }

    TIME_TYPE_MAP = {
        "日": SceneTime.DAY,
        "白天": SceneTime.DAY,
        "夜": SceneTime.NIGHT,
        "晚上": SceneTime.NIGHT,
        "夜晚": SceneTime.NIGHT,
        "晨": SceneTime.DAWN,
        "黎明": SceneTime.DAWN,
        "清晨": SceneTime.DAWN,
        "早晨": SceneTime.DAWN,
        "黄昏": SceneTime.DUSK,
        "傍晚": SceneTime.EVENING,
    }

    @classmethod
    def parse(cls, script_text: str) -> tuple[str, list[dict[str, Any]]]:
        lines = script_text.strip().split("\n")
        title = ""
        scenes = []
        current_scene = None
        current_content_lines = []

        for line in lines:
            line = line.strip()

            if not line:
                if current_content_lines:
                    current_content_lines.append("")
                continue

            if not title and not line.startswith("第"):
                title = line
                continue

            if line in ["剧终", "全剧终", "（剧终）"]:
                break

            match = cls.SCENE_HEADER_PATTERN.match(line)
            if match:
                if current_scene:
                    current_scene["content"] = "\n".join(current_content_lines).strip()
                    scenes.append(current_scene)
                    current_content_lines = []

                scene_number = int(match.group(1))
                location_type_raw = match.group(2)
                location = match.group(3).strip()
                time_raw = match.group(4).strip()

                location_type = cls.LOCATION_TYPE_MAP.get(
                    location_type_raw, SceneLocation.INTERIOR
                ).value

                time_type = SceneTime.DAY
                time_detail = ""

                for key, enum_val in cls.TIME_TYPE_MAP.items():
                    if key in time_raw:
                        time_type = enum_val
                        if time_raw != key:
                            time_detail = time_raw
                        break
                else:
                    time_type = SceneTime.CUSTOM
                    time_detail = time_raw

                current_scene = {
                    "scene_number": scene_number,
                    "location_type": location_type,
                    "location": location,
                    "time_type": time_type.value,
                    "time_detail": time_detail,
                }
            else:
                if current_scene is not None:
                    current_content_lines.append(line)

        if current_scene:
            current_scene["content"] = "\n".join(current_content_lines).strip()
            scenes.append(current_scene)

        logger.info(f"解析剧本完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes
