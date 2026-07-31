import re

from models.enums import ShotSize


class ShotParser:
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
        shots = []
        lines = markdown_text.strip().split("\n")

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

    @classmethod
    def parse_characters(cls, markdown_text: str) -> list[dict]:
        characters = []
        lines = markdown_text.strip().split("\n")

        in_char_table = False
        header_found = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if "角色名" in line and "引用代号" in line:
                header_found = True
                in_char_table = True
                continue

            if in_char_table and ":---" in line:
                continue

            if in_char_table and line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                if len(cells) >= 3:
                    name = cells[0]
                    ref_code = cells[1]
                    description = cells[2]
                    if name and ref_code:
                        characters.append({
                            "name": name,
                            "ref_code": ref_code,
                            "description": description,
                        })
            elif in_char_table and not line.startswith("|"):
                in_char_table = False

        return characters
