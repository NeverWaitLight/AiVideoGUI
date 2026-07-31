from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class PromptTemplate:
    def __init__(self, config: dict[str, Any]) -> None:
        self.system_prompt = config["system_prompt"]
        self.few_shot_examples = config.get("few_shot_examples", [])
        self.user_prompt_template = config["user_prompt_template"]

    def build_messages(self, **kwargs) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]

        for example in self.few_shot_examples:
            messages.append({"role": "user", "content": example["user"]})
            messages.append({"role": "assistant", "content": example["assistant"]})

        user_content = self.user_prompt_template.format(**kwargs)
        messages.append({"role": "user", "content": user_content})

        return messages


class PromptTemplateManager:
    def __init__(self, templates_dir: Path | str) -> None:
        self._templates_dir = Path(templates_dir)
        self._templates: dict[str, PromptTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        if not self._templates_dir.exists():
            logger.warning(f"模板目录不存在：{self._templates_dir}")
            return

        yaml_files = list(self._templates_dir.glob("*.yaml"))
        logger.info(f"从 {self._templates_dir} 加载 {len(yaml_files)} 个模板文件")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                template_name = yaml_file.stem
                self._templates[template_name] = PromptTemplate(config)
                logger.debug(f"加载模板：{template_name}")

            except Exception as e:
                logger.exception(f"加载模板文件失败：{yaml_file}")
                raise RuntimeError(f"加载模板文件 {yaml_file} 失败：{e}")

        logger.info(f"成功加载 {len(self._templates)} 个提示词模板")

    def get_template(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise KeyError(f"模板不存在：{name}，可用模板：{list(self._templates.keys())}")
        return self._templates[name]

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())
