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

        返回：分镜数据列表，每个元素为字典：
        {
            "shot_number": int,
            "shot_size": str (枚举值),
            "visual_content": str,
            "camera_movement": str,
            "sound_dialogue": str,
            "duration": float,
            "color_lighting": str
        }
        """
        shots = []

        # 匹配 Markdown 表格行（跳过表头和分隔线）
        # 格式：| 镜头序号 | 景别 | 画面内容描述 | 运镜方式 | 音效/台词 | 时长(秒) | 色调/光影 |
        lines = markdown_text.strip().split("\n")

        for line in lines:
            line = line.strip()

            # 跳过空行、表头行、分隔行
            if not line or line.startswith("#") or "镜头序号" in line or ":---" in line:
                continue

            # 解析表格行
            if line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]  # 去除首尾的空元素

                # 至少需要 7 列
                if len(cells) < 7:
                    continue

                # 提取数据
                try:
                    shot_number_str = cells[0]
                    shot_size_str = cells[1]
                    visual_content = cells[2]
                    camera_movement = cells[3]
                    sound_dialogue = cells[4]
                    duration_str = cells[5]
                    color_lighting = cells[6]

                    # 解析镜头序号
                    shot_number = int(re.search(r"\d+", shot_number_str).group())

                    # 解析景别（支持带说明的格式，如"特写（面部特写）"）
                    shot_size_key = shot_size_str.split("（")[0].split("(")[0].strip()
                    shot_size = cls.SHOT_SIZE_MAP.get(shot_size_key, ShotSize.MEDIUM_SHOT)

                    # 解析时长
                    duration_match = re.search(r"[\d.]+", duration_str)
                    duration = float(duration_match.group()) if duration_match else 0.0

                    shots.append({
                        "shot_number": shot_number,
                        "shot_size": shot_size.value,
                        "visual_content": visual_content,
                        "camera_movement": camera_movement,
                        "sound_dialogue": sound_dialogue,
                        "duration": duration,
                        "color_lighting": color_lighting,
                    })

                except (ValueError, AttributeError, IndexError):
                    # 解析失败，跳过该行
                    continue

        return shots
