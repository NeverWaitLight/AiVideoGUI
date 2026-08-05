from models.scene import Scene
from models.storyboard import Storyboard


class VideoPromptBuilder:
    @staticmethod
    def build_shot_prompt(
        storyboard: Storyboard,
        scene: Scene | None = None,
        prev_shot: Storyboard | None = None,
        next_shot: Storyboard | None = None,
        reference_images: list[dict[str, str]] | None = None,
        visual_style: str | None = None,
    ) -> str:
        sections = []

        if scene:
            scene_context = VideoPromptBuilder._build_scene_context(scene)
            if scene_context:
                sections.append(f"【场景上下文】\n{scene_context}")

        if visual_style:
            sections.append(f"【视觉风格】\n{visual_style}")

        if reference_images:
            ref_desc = VideoPromptBuilder._build_reference_images_desc(reference_images)
            if ref_desc:
                sections.append(f"【参考图片说明】\n{ref_desc}")

        sections.append(f"【镜头画面】\n{storyboard.visual_content.strip()}")

        shot_params = []

        shot_size_map = {
            "extreme_close_up": "特写",
            "close_up": "近景",
            "medium_shot": "中景",
            "full_shot": "全景",
            "long_shot": "远景",
            "extreme_long_shot": "大远景",
        }
        shot_size_cn = shot_size_map.get(storyboard.shot_size.value, "中景")
        shot_params.append(f"景别：{shot_size_cn}")

        if storyboard.camera_movement:
            shot_params.append(f"运镜：{storyboard.camera_movement}")

        if storyboard.duration > 0:
            shot_params.append(f"时长：{storyboard.duration}秒")

        if shot_params:
            sections.append(f"【镜头参数】\n{' | '.join(shot_params)}")

        if storyboard.dialogue and storyboard.dialogue.strip():
            sections.append(f"【台词】\n{storyboard.dialogue.strip()}")

        if storyboard.sound_effect and storyboard.sound_effect.strip():
            sections.append(f"【音效】\n{storyboard.sound_effect.strip()}")

        continuity_hints = []
        if prev_shot and prev_shot.visual_content.strip():
            prev_preview = prev_shot.visual_content.strip()[:80]
            if len(prev_shot.visual_content.strip()) > 80:
                prev_preview += "..."
            continuity_hints.append(f"前一镜：{prev_preview}")

        if next_shot and next_shot.visual_content.strip():
            next_preview = next_shot.visual_content.strip()[:80]
            if len(next_shot.visual_content.strip()) > 80:
                next_preview += "..."
            continuity_hints.append(f"后一镜：{next_preview}")

        if continuity_hints:
            sections.append(f"【连贯性提示】\n{' | '.join(continuity_hints)}")

        if storyboard.notes and storyboard.notes.strip():
            sections.append(f"【备注】\n{storyboard.notes.strip()}")

        return "\n\n".join(sections)

    @staticmethod
    def _build_reference_images_desc(reference_images: list[dict[str, str]]) -> str:
        if not reference_images:
            return ""

        lines = []
        for i, ref in enumerate(reference_images, 1):
            ref_type = ref.get("type", "unknown")
            description = ref.get("description", "")

            if ref_type == "design":
                lines.append(f"图{i}：本镜头的分镜设计图，请参考其构图、机位、光线、色调和整体氛围。{description}")
            elif ref_type == "character":
                char_name = ref.get("character_name", "角色")
                lines.append(f"图{i}：{char_name}的角色设计图，请严格参考其外观、服装、神态等视觉特征。{description}")
            else:
                lines.append(f"图{i}：参考图片。{description}")

        return "\n".join(lines)

    @staticmethod
    def _build_scene_context(scene: Scene) -> str:
        parts = []

        parts.append(f"第 {scene.scene_number} 场")

        location_type_map = {
            "interior": "内景",
            "exterior": "外景",
            "interior_exterior": "内/外景",
        }
        location_type = location_type_map.get(scene.location_type.value, "")
        if location_type:
            parts.append(location_type)
        parts.append(scene.location)

        time_map = {
            "day": "日",
            "night": "夜",
            "dawn": "晨",
            "dusk": "黄昏",
            "evening": "傍晚",
            "custom": scene.time_detail if scene.time_detail else "",
        }
        time_str = time_map.get(scene.time_type.value, "")
        if time_str:
            parts.append(time_str)

        location_time_line = " · ".join(parts)

        scene_lines = [location_time_line]
        if scene.content and scene.content.strip():
            content_preview = scene.content.strip()[:200]
            if len(scene.content.strip()) > 200:
                content_preview += "..."
            scene_lines.append(content_preview)

        return "\n".join(scene_lines)
