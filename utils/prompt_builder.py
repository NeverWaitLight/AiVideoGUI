"""视频生成 Prompt 构建工具"""

from models.scene import Scene
from models.storyboard import Storyboard


class VideoPromptBuilder:
    """视频生成 Prompt 构建器（结构化、易读）"""

    @staticmethod
    def build_shot_prompt(
        storyboard: Storyboard,
        scene: Scene | None = None,
        prev_shot: Storyboard | None = None,
        next_shot: Storyboard | None = None,
    ) -> str:
        """
        构建分镜视频生成 Prompt（结构化格式）。

        Args:
            storyboard: 当前分镜
            scene: 当前场次（可选，提供场景上下文）
            prev_shot: 前一个分镜（可选，提供视觉连贯性）
            next_shot: 后一个分镜（可选，提供视觉连贯性）

        Returns:
            结构化的视频生成 Prompt
        """
        sections = []

        # ========== 1. 场景上下文（如果有场次信息）==========
        if scene:
            scene_context = VideoPromptBuilder._build_scene_context(scene)
            if scene_context:
                sections.append(f"【场景上下文】\n{scene_context}")

        # ========== 2. 当前镜头画面描述（主要内容）==========
        sections.append(f"【镜头画面】\n{storyboard.visual_content.strip()}")

        # ========== 3. 镜头参数 ==========
        shot_params = []

        # 景别
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

        # 运镜
        if storyboard.camera_movement:
            shot_params.append(f"运镜：{storyboard.camera_movement}")

        # 时长
        if storyboard.duration > 0:
            shot_params.append(f"时长：{storyboard.duration}秒")

        if shot_params:
            sections.append(f"【镜头参数】\n{' | '.join(shot_params)}")

        # ========== 4. 台词/对白（如果有）==========
        if storyboard.dialogue and storyboard.dialogue.strip():
            sections.append(f"【台词】\n{storyboard.dialogue.strip()}")

        # ========== 5. 音效提示（如果有）==========
        if storyboard.sound_effect and storyboard.sound_effect.strip():
            sections.append(f"【音效】\n{storyboard.sound_effect.strip()}")

        # ========== 6. 视觉连贯性提示（相邻镜头上下文）==========
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

        # ========== 7. 备注（如果有）==========
        if storyboard.notes and storyboard.notes.strip():
            sections.append(f"【备注】\n{storyboard.notes.strip()}")

        # 组合所有段落（使用双换行分隔，清晰易读）
        return "\n\n".join(sections)

    @staticmethod
    def _build_scene_context(scene: Scene) -> str:
        """构建场景上下文描述。"""
        parts = []

        # 场次号
        parts.append(f"第 {scene.scene_number} 场")

        # 内外景 + 地点
        location_type_map = {
            "interior": "内景",
            "exterior": "外景",
            "interior_exterior": "内/外景",
        }
        location_type = location_type_map.get(scene.location_type.value, "")
        if location_type:
            parts.append(location_type)
        parts.append(scene.location)

        # 时间
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

        # 场次内容（剧本描述）
        scene_lines = [location_time_line]
        if scene.content and scene.content.strip():
            # 截取前 200 字符（避免过长）
            content_preview = scene.content.strip()[:200]
            if len(scene.content.strip()) > 200:
                content_preview += "..."
            scene_lines.append(content_preview)

        return "\n".join(scene_lines)
