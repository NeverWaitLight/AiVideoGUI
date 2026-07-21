"""剧本解析工具：将 AI 生成的剧本文本解析为场次结构。"""

import logging
import re
from typing import Any

from models.data_models import SceneLocation, SceneTime

logger = logging.getLogger(__name__)


class ScriptParser:
    """剧本解析器：解析标准影视剧本格式文本。"""

    # 场景标题正则：第X场  内景/外景  地点  -  时间
    SCENE_HEADER_PATTERN = re.compile(
        r"第\s*(\d+)\s*场\s+(内景|外景|内景/外景)\s+(.+?)\s*[-—]\s*(.+)",
        re.IGNORECASE,
    )

    # 内外景映射
    LOCATION_TYPE_MAP = {
        "内景": SceneLocation.INTERIOR,
        "外景": SceneLocation.EXTERIOR,
        "内景/外景": SceneLocation.INTERIOR_EXTERIOR,
    }

    # 时间类型映射
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
        """解析剧本文本为结构化数据。

        Args:
            script_text: 完整的剧本文本

        Returns:
            (剧本标题, 场次列表)，其中每个场次是字典：
            {
                "scene_number": int,
                "location_type": str,
                "location": str,
                "time_type": str,
                "time_detail": str,
                "content": str,
            }
        """
        lines = script_text.strip().split("\n")
        title = ""
        scenes = []
        current_scene = None
        current_content_lines = []

        for line in lines:
            line = line.strip()

            # 跳过空行
            if not line:
                if current_content_lines:
                    current_content_lines.append("")
                continue

            # 提取标题（第一行非空行）
            if not title and not line.startswith("第"):
                title = line
                continue

            # 跳过"剧终"
            if line in ["剧终", "全剧终", "（剧终）"]:
                break

            # 匹配场景标题
            match = cls.SCENE_HEADER_PATTERN.match(line)
            if match:
                # 保存上一个场次
                if current_scene:
                    current_scene["content"] = "\n".join(current_content_lines).strip()
                    scenes.append(current_scene)
                    current_content_lines = []

                # 解析新场次
                scene_number = int(match.group(1))
                location_type_raw = match.group(2)
                location = match.group(3).strip()
                time_raw = match.group(4).strip()

                # 映射内外景类型
                location_type = cls.LOCATION_TYPE_MAP.get(
                    location_type_raw, SceneLocation.INTERIOR
                ).value

                # 映射时间类型
                time_type = SceneTime.DAY  # 默认白天
                time_detail = ""

                for key, enum_val in cls.TIME_TYPE_MAP.items():
                    if key in time_raw:
                        time_type = enum_val
                        # 如果有更详细的时间描述，保存到 time_detail
                        if time_raw != key:
                            time_detail = time_raw
                        break
                else:
                    # 没有匹配到标准时间类型，作为自定义时间
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
                # 场次内容
                if current_scene is not None:
                    current_content_lines.append(line)

        # 保存最后一个场次
        if current_scene:
            current_scene["content"] = "\n".join(current_content_lines).strip()
            scenes.append(current_scene)

        logger.info(f"解析剧本完成：标题='{title}'，共 {len(scenes)} 场")
        return title, scenes
