from prompts.manager import PromptTemplateManager


class TextPromptBuilder:
    """文本大模型提示词构建器（统一入口）"""

    def __init__(self, template_manager: PromptTemplateManager) -> None:
        self._template_manager = template_manager

    def build_chat_messages(
        self,
        user_input: str,
    ) -> list[dict[str, str]]:
        """构建聊天对话消息"""
        template = self._template_manager.get_template("chat")
        return template.build_messages(user_input=user_input)

    def build_outline_optimization_messages(
        self,
        original_content: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建大纲优化消息"""
        template = self._template_manager.get_template("outline_optimization")
        return template.build_messages(
            original_content=original_content if original_content.strip() else "（空大纲）",
            user_requirement=user_requirement,
        )

    def build_script_generation_messages(
        self,
        outline_content: str,
    ) -> list[dict[str, str]]:
        """构建剧本生成消息"""
        template = self._template_manager.get_template("script_generation")
        return template.build_messages(
            outline_content=outline_content if outline_content.strip() else "（空大纲，请根据常规视频创作流程生成一个简单的剧本示例）"
        )

    def build_storyboard_generation_messages(
        self,
        script_content: str,
        art_style: str = "",
    ) -> list[dict[str, str]]:
        """构建分镜生成消息"""
        template = self._template_manager.get_template("storyboard_generation_with_characters")
        return template.build_messages(
            script_content=script_content if script_content.strip() else "（空剧本）",
            art_style=art_style if art_style.strip() else "通用电影感写实风格",
        )

    def build_design_image_prompt_messages(
        self,
        visual_content: str,
        shot_size: str = "",
        camera_movement: str = "",
        dialogue: str = "",
        notes: str = "",
        character_info: str = "",
    ) -> list[dict[str, str]]:
        """构建分镜设计图提示词生成消息"""
        template = self._template_manager.get_template("image_prompt_generation")
        return template.build_messages(
            visual_content=visual_content,
            shot_size=shot_size or "中景",
            camera_movement=camera_movement or "固定",
            dialogue=dialogue or "无",
            notes=notes or "无特殊要求",
            character_info=character_info or "无额外角色信息",
        )

    def build_character_design_image_prompt_messages(
        self,
        character_name: str,
        description: str,
        user_requirement: str = "",
    ) -> list[dict[str, str]]:
        """构建角色设计图提示词生成消息"""
        template = self._template_manager.get_template("character_image_prompt_generation")
        req_text = f"\n【用户补充要求】\n{user_requirement}" if user_requirement else ""
        return template.build_messages(
            character_name=character_name,
            description=description,
            user_requirement=req_text,
        )

    def build_screenplay_optimization_messages(
        self,
        outline_content: str,
        current_script: str,
        user_requirement: str,
    ) -> list[dict[str, str]]:
        """构建剧本优化消息"""
        template = self._template_manager.get_template("screenplay_optimization")
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
        template = self._template_manager.get_template("character_generation")
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
        template = self._template_manager.get_template("character_optimization")
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
        template = self._template_manager.get_template("storyboard_optimization")
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
        template = self._template_manager.get_template("character_description_refine")
        return template.build_messages(
            character_name=character_name,
            current_description=current_description,
            user_requirement=user_requirement,
        )
