"""角色数据解析器"""

import json
import re
from loguru import logger


class CharacterParser:
    """解析 LLM 返回的角色数据"""

    @staticmethod
    def parse(response_text: str) -> list[dict]:
        """解析 JSON 格式的角色列表

        Args:
            response_text: LLM 返回的原始文本（JSON 数组或 {"characters": [...]} 对象）

        Returns:
            角色列表，每个角色包含 name, ref_code, description 字段

        Raises:
            ValueError: 解析失败时抛出
        """
        response_text = response_text.strip()

        # 清洗 Markdown 代码块标记
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # 尝试直接解析 JSON
        characters = CharacterParser._try_parse_json(response_text)
        if characters is not None:
            logger.info(f"解析角色完成：共 {len(characters)} 个角色")
            return characters

        # 尝试从文本中提取 JSON 块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            characters = CharacterParser._try_parse_json(json_match.group(1))
            if characters is not None:
                logger.info(f"从代码块中提取角色完成：共 {len(characters)} 个角色")
                return characters

        # 尝试查找 JSON 数组或对象
        json_match = re.search(r'[\[{][\s\S]*[\]}]', response_text)
        if json_match:
            characters = CharacterParser._try_parse_json(json_match.group(0))
            if characters is not None:
                logger.info(f"从文本中提取角色完成：共 {len(characters)} 个角色")
                return characters

        logger.error(f"无法解析角色数据，原始文本:\n{response_text[:500]}")
        raise ValueError("无法解析角色数据，格式不正确")

    @staticmethod
    def _try_parse_json(text: str) -> list[dict] | None:
        """尝试解析 JSON，返回角色列表或 None"""
        try:
            decoder = json.JSONDecoder(strict=False)
            data = decoder.decode(text)
        except json.JSONDecodeError:
            return None

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "characters" in data:
            items = data["characters"]
        else:
            return None

        return CharacterParser._validate_characters(items)

    @staticmethod
    def _validate_characters(data: list[dict]) -> list[dict]:
        """验证并规范化角色数据"""
        validated = []
        for item in data:
            if not isinstance(item, dict):
                continue

            name = (item.get("name") or item.get("角色名") or "").strip()
            ref_code = (item.get("ref_code") or item.get("引用代号") or "").strip()
            description = (item.get("description") or item.get("形象描述") or "").strip()
            voice_tone = (item.get("voice_tone") or item.get("音色描述") or "").strip()

            if not name or not ref_code:
                logger.warning(f"跳过无效角色数据: {item}")
                continue

            validated.append({
                "name": name,
                "ref_code": ref_code,
                "description": description,
                "voice_tone": voice_tone,
            })

        return validated if validated else None
