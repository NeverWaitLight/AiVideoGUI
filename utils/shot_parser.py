"""分镜头脚本解析器，将 AI 生成的 Markdown 表格解析为结构化数据。"""

import re

from models.data_models import ShotSize


class ShotParser:
    """解析 AI 生成的分镜头脚本（Markdown 表格格式）。"""

    # 景别映射：中文 -> 枚举
    SHOT_SIZE_MAP = {
        "特写": ShotSize.EXTREME_CLOSE_UP,
        "极近特写": ShotSize.EXTREME_CLOSE_UP,
        "近景": ShotSize.CLOSE_UP,
        "中景": ShotSize.MEDIUM_SHOT,
        "全景": ShotSize.FULL_SHOT,
        "远景": ShotSize.LONG_SHOT,
        "大远景": ShotSize.EXTREME_LONG_SHOT,
    }

    @classmethod
    def parse(cls, markdown_text: str) -> list[dict]:
        """
        解析 Markdown 表格格式的分镜脚本。

        支持两种格式：
        - 8 列（含场次）：| 场次 | 镜头序号 | 景别 | 画面内容 | 运镜 | 音效/台词 | 时长 | 色调 |
        - 7 列（无场次）：| 镜头序号 | 景别 | 画面内容 | 运镜 | 音效/台词 | 时长 | 色调 |

        返回：分镜数据列表，每个元素为字典。
        """
        shots = []
        lines = markdown_text.strip().split("\n")

        # 检测表头格式，判断是否包含场次列
        has_scene_column = False
        for line in lines:
            stripped = line.strip()
            if "镜头序号" in stripped and "场次" in stripped:
                has_scene_column = True
                break
            if "镜头序号" in stripped:
                break

        for line in lines:
            line = line.strip()

            # 跳过空行、表头行、分隔行
            if not line or line.startswith("#") or "镜头序号" in line or ":---" in line:
                continue

            if line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]

                if has_scene_column:
                    if len(cells) < 8:
                        continue
                    try:
                        scene_number = int(re.search(r"\d+", cells[0]).group())
                        shot_number = int(re.search(r"\d+", cells[1]).group())
                        shot_size_str = cells[2]
                        visual_content = cells[3]
                        camera_movement = cells[4]
                        sound_dialogue = cells[5]
                        duration_str = cells[6]
                        color_lighting = cells[7]
                    except (ValueError, AttributeError, IndexError):
                        continue
                else:
                    if len(cells) < 7:
                        continue
                    try:
                        scene_number = 1
                        shot_number = int(re.search(r"\d+", cells[0]).group())
                        shot_size_str = cells[1]
                        visual_content = cells[2]
                        camera_movement = cells[3]
                        sound_dialogue = cells[4]
                        duration_str = cells[5]
                        color_lighting = cells[6]
                    except (ValueError, AttributeError, IndexError):
                        continue

                shot_size_key = shot_size_str.split("（")[0].split("(")[0].strip()
                shot_size = cls.SHOT_SIZE_MAP.get(shot_size_key, ShotSize.MEDIUM_SHOT)

                duration_match = re.search(r"[\d.]+", duration_str)
                duration = float(duration_match.group()) if duration_match else 0.0

                shots.append({
                    "scene_number": scene_number,
                    "shot_number": shot_number,
                    "shot_size": shot_size.value,
                    "visual_content": visual_content,
                    "camera_movement": camera_movement,
                    "sound_dialogue": sound_dialogue,
                    "duration": duration,
                    "color_lighting": color_lighting,
                })

        return shots
