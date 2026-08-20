from __future__ import annotations

from typing import TYPE_CHECKING

from prompts.manager import PromptTemplateManager

if TYPE_CHECKING:
    from models.scene import Scene
    from models.storyboard import Storyboard


class ChatPromptBuilder:
    """文本大模型提示词构建器（统一入口）"""

    def __init__(self, template_manager: PromptTemplateManager) -> None:
        self._template_manager = template_manager

    @staticmethod
    def _normalize_visual_style(visual_style: str | None) -> str:
        style = (visual_style or "").strip()
        if not style or style == "默认":
            return ""
        return style

    @staticmethod
    def _build_visual_style_block(
        visual_style: str,
        style_instruction: str,
        *,
        style_label: str = "画面风格",
    ) -> str:
        if not visual_style:
            return ""
        return (
            f"\n【{style_label}】{visual_style}\n\n"
            f"【画面风格要求】\n{style_instruction}\n"
        )

    def build_outline_optimization_messages(
        self,
        original_content: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建大纲优化消息"""
        template = self._template_manager.get_template("outline_optimize")
        return template.build_messages(
            original_content=original_content if original_content.strip() else "（空大纲）",
            user_requirement=user_requirement,
        )

    def build_script_generation_messages(
        self,
        outline_content: str,
    ) -> list[dict[str, str]]:
        """构建剧本生成消息"""
        template = self._template_manager.get_template("screenplay_generate")
        return template.build_messages(
            outline_content=outline_content if outline_content.strip() else "（空大纲，请根据常规视频创作流程生成一个简单的剧本示例）"
        )

    def build_storyboard_generation_messages(
        self,
        script_content: str,
        art_style: str = "",
    ) -> list[dict[str, str]]:
        """构建分镜生成消息"""
        template = self._template_manager.get_template("storyboard_generate")
        return template.build_messages(
            script_content=script_content if script_content.strip() else "（空剧本）",
            art_style=art_style if art_style.strip() else "通用电影感写实风格",
        )

    def build_design_image_prompt_messages(
        self,
        content: str,
        shot_size: str = "",
        camera_movement: str = "",
        notes: str = "",
        character_info: str = "",
        visual_style: str = "",
    ) -> list[dict[str, str]]:
        """构建分镜设计图提示词生成消息"""
        template = self._template_manager.get_template("storyboard_image_prompt")
        style = self._normalize_visual_style(visual_style)
        style_instruction = (
            f"整体画面采用【{style}】风格，画面构图、光影、色调与质感应符合该风格特点"
            if style
            else ""
        )
        return template.build_messages(
            content=content,
            shot_size=shot_size or "中景",
            camera_movement=camera_movement or "固定",
            notes=notes or "无特殊要求",
            character_info=character_info or "无额外角色信息",
            visual_style_block=self._build_visual_style_block(style, style_instruction),
        )

    def build_character_design_image_prompt_messages(
        self,
        character_name: str,
        description: str,
        user_requirement: str = "",
        visual_style: str = "",
    ) -> list[dict[str, str]]:
        """构建角色设计图提示词生成消息"""
        template = self._template_manager.get_template("character_image_prompt")
        req_text = f"\n【用户补充要求】\n{user_requirement}" if user_requirement else ""
        style = self._normalize_visual_style(visual_style)
        style_instruction = (
            f"整体画面采用【{style}】风格，在保持角色三视图规范的前提下，"
            f"画面色调、光影、质感应符合该风格特点"
            if style
            else ""
        )
        return template.build_messages(
            character_name=character_name,
            description=description,
            visual_style_block=self._build_visual_style_block(style, style_instruction),
            user_requirement=req_text,
        )

    def build_screenplay_optimization_messages(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建剧本优化消息"""
        template = self._template_manager.get_template("screenplay_optimize")
        return template.build_messages(
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_requirement,
        )

    def build_character_generation_messages(
        self,
        outline_content: str,
        script_content: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建角色生成消息"""
        template = self._template_manager.get_template("character_generate")
        return template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            user_requirement=user_requirement,
        )

    def build_character_optimization_messages(
        self,
        outline_content: str,
        script_content: str,
        current_characters: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建角色优化消息"""
        template = self._template_manager.get_template("character_optimize")
        return template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            current_characters=current_characters,
            user_requirement=user_requirement,
        )

    def build_storyboard_optimization_messages(
        self,
        outline_content: str,
        script_content: str,
        character_content: str,
        current_storyboard: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建分镜优化消息"""
        template = self._template_manager.get_template("storyboard_optimize")
        return template.build_messages(
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_requirement,
        )

    def build_character_description_refine_messages(
        self,
        character_name: str,
        current_description: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建角色描述优化消息"""
        template = self._template_manager.get_template("character_refine")
        return template.build_messages(
            character_name=character_name,
            current_description=current_description,
            user_requirement=user_requirement,
        )

    def build_cover_image_prompt_messages(
        self,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_info: str,
        visual_style: str = "",
    ) -> list[dict[str, str]]:
        """构建项目封面图提示词生成消息"""
        template = self._template_manager.get_template("project_cover_image_prompt")
        style = self._normalize_visual_style(visual_style)
        style_instruction = (
            f"整体画面采用【{style}】风格，色调、光影、质感应符合该风格特点"
            if style
            else ""
        )
        return template.build_messages(
            project_name=project_name,
            aspect_ratio=aspect_ratio,
            outline_content=outline_content if outline_content.strip() else "（暂无大纲）",
            character_info=character_info if character_info.strip() else "无角色信息",
            visual_style_block=self._build_visual_style_block(
                style, style_instruction, style_label="视觉风格"
            ),
        )

    def build_video_prompt_clean_messages(
        self,
        original_prompt: str,
    ) -> list[dict[str, str]]:
        """构建视频提示词清理消息"""
        template = self._template_manager.get_template("storyboard_video_prompt_clean")
        return template.build_messages(original_prompt=original_prompt)

    def assemble_video_shot_prompt(
        self,
        storyboard: Storyboard,
        scene: Scene | None = None,
        prev_shot: Storyboard | None = None,
        next_shot: Storyboard | None = None,
        reference_images: list[dict[str, str]] | None = None,
        visual_style: str | None = None,
    ) -> str:
        from prompts.video_prompt_builder import VideoPromptBuilder

        return VideoPromptBuilder.build_shot_prompt(
            storyboard,
            scene,
            prev_shot,
            next_shot,
            reference_images=reference_images,
            visual_style=visual_style,
        )
