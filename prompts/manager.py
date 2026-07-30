"""提示词模板管理器。

支持从 YAML 配置文件加载和管理不同任务的系统提示词和 few-shot 示例。
"""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class PromptTemplate:
    """单个提示词模板。

    包含系统提示词、few-shot 示例和用户提示词模板。
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """初始化提示词模板。

        Args:
            config: YAML 配置字典，包含以下字段：
                - system_prompt: 系统提示词（必需）
                - few_shot_examples: few-shot 示例列表（可选）
                - user_prompt_template: 用户提示词模板（必需）
        """
        self.system_prompt = config["system_prompt"]
        self.few_shot_examples = config.get("few_shot_examples", [])
        self.user_prompt_template = config["user_prompt_template"]

    def build_messages(self, **kwargs) -> list[dict[str, str]]:
        """构建完整的消息列表。

        Args:
            **kwargs: 用于填充用户提示词模板的参数

        Returns:
            消息列表，格式为 [{"role": "system/user/assistant", "content": "..."}]
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # 插入 few-shot 示例
        for example in self.few_shot_examples:
            messages.append({"role": "user", "content": example["user"]})
            messages.append({"role": "assistant", "content": example["assistant"]})

        # 填充用户提示词模板
        user_content = self.user_prompt_template.format(**kwargs)
        messages.append({"role": "user", "content": user_content})

        return messages


class PromptTemplateManager:
    """提示词模板管理器。

    负责加载和管理所有提示词模板。
    """

    def __init__(self, templates_dir: Path | str) -> None:
        """初始化模板管理器。

        Args:
            templates_dir: 模板配置文件目录路径
        """
        self._templates_dir = Path(templates_dir)
        self._templates: dict[str, PromptTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """从目录加载所有 YAML 模板文件。"""
        if not self._templates_dir.exists():
            logger.warning(f"模板目录不存在：{self._templates_dir}")
            return

        yaml_files = list(self._templates_dir.glob("*.yaml"))
        logger.info(f"从 {self._templates_dir} 加载 {len(yaml_files)} 个模板文件")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                template_name = yaml_file.stem  # 文件名（不含扩展名）
                self._templates[template_name] = PromptTemplate(config)
                logger.debug(f"加载模板：{template_name}")

            except Exception as e:
                logger.exception(f"加载模板文件失败：{yaml_file}")
                raise RuntimeError(f"加载模板文件 {yaml_file} 失败：{e}")

        logger.info(f"成功加载 {len(self._templates)} 个提示词模板")

    def get_template(self, name: str) -> PromptTemplate:
        """获取指定名称的模板。

        Args:
            name: 模板名称（YAML 文件名，不含扩展名）

        Returns:
            PromptTemplate 实例

        Raises:
            KeyError: 模板不存在
        """
        if name not in self._templates:
            raise KeyError(f"模板不存在：{name}，可用模板：{list(self._templates.keys())}")
        return self._templates[name]

    def list_templates(self) -> list[str]:
        """列出所有可用的模板名称。"""
        return list(self._templates.keys())
