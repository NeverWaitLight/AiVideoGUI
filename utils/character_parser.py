"""角色数据解析器"""

import json
import re
from loguru import logger


class CharacterParser:
    """解析 LLM 返回的角色数据"""

    @staticmethod
    def parse(response_text: str) -> list[dict]:
        """解析角色数据

        支持两种格式：
        1. JSON 数组: [{"name": "...", "ref_code": "...", "description": "..."}]
        2. Markdown 表格:
           | 角色名 | 引用代号 | 形象描述 |
           | --- | --- | --- |
           | 张三 | CHAR_A | ... |

        Args:
            response_text: LLM 返回的原始文本

        Returns:
            角色列表，每个角色包含 name, ref_code, description 字段

        Raises:
            ValueError: 解析失败时抛出
        """
        response_text = response_text.strip()

        # 尝试解析 JSON 格式
        try:
            characters = CharacterParser._parse_json(response_text)
            if characters:
                logger.info(f"成功解析 JSON 格式角色数据，共 {len(characters)} 个角色")
                return characters
        except Exception as e:
            logger.debug(f"JSON 解析失败: {e}")

        # 尝试解析 Markdown 表格格式
        try:
            characters = CharacterParser._parse_markdown_table(response_text)
            if characters:
                logger.info(f"成功解析 Markdown 表格格式角色数据，共 {len(characters)} 个角色")
                return characters
        except Exception as e:
            logger.debug(f"Markdown 表格解析失败: {e}")

        # 所有格式都失败
        logger.error(f"无法解析角色数据，原始文本:\n{response_text[:500]}")
        raise ValueError("无法解析角色数据，格式不正确")

    @staticmethod
    def _parse_json(text: str) -> list[dict] | None:
        """解析 JSON 格式"""
        # 尝试直接解析
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return CharacterParser._validate_characters(data)
            elif isinstance(data, dict) and "characters" in data:
                return CharacterParser._validate_characters(data["characters"])
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return CharacterParser._validate_characters(data)
            except json.JSONDecodeError:
                pass

        # 尝试查找 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return CharacterParser._validate_characters(data)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _parse_markdown_table(text: str) -> list[dict] | None:
        """解析 Markdown 表格格式"""
        lines = text.split('\n')

        # 查找表格开始（包含 | 的行）
        table_lines = [line for line in lines if '|' in line]
        if len(table_lines) < 3:  # 至少需要：表头 + 分隔线 + 1行数据
            return None

        # 解析表头
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        # 查找列索引（支持不同的列名）
        name_idx = CharacterParser._find_column_index(headers, ['角色名', '姓名', 'name', '名称'])
        ref_code_idx = CharacterParser._find_column_index(headers, ['引用代号', '代号', 'ref_code', '引用'])
        desc_idx = CharacterParser._find_column_index(headers, ['形象描述', '描述', 'description', '外貌'])

        if name_idx is None or ref_code_idx is None or desc_idx is None:
            logger.warning(f"表格列名不匹配: {headers}")
            return None

        # 解析数据行（跳过表头和分隔线）
        characters = []
        for line in table_lines[2:]:
            if not line.strip() or line.strip().startswith('|---'):
                continue

            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) < max(name_idx, ref_code_idx, desc_idx) + 1:
                continue

            character = {
                "name": cells[name_idx].strip(),
                "ref_code": cells[ref_code_idx].strip(),
                "description": cells[desc_idx].strip(),
            }

            if character["name"] and character["ref_code"]:
                characters.append(character)

        return characters if characters else None

    @staticmethod
    def _find_column_index(headers: list[str], possible_names: list[str]) -> int | None:
        """查找列索引"""
        for name in possible_names:
            for i, header in enumerate(headers):
                if name.lower() in header.lower():
                    return i
        return None

    @staticmethod
    def _validate_characters(data: list[dict]) -> list[dict]:
        """验证并规范化角色数据"""
        validated = []
        for item in data:
            if not isinstance(item, dict):
                continue

            # 提取必需字段
            name = item.get("name") or item.get("角色名") or item.get("姓名") or ""
            ref_code = item.get("ref_code") or item.get("引用代号") or item.get("代号") or ""
            description = item.get("description") or item.get("形象描述") or item.get("描述") or ""

            if not name or not ref_code:
                logger.warning(f"跳过无效角色数据: {item}")
                continue

            validated.append({
                "name": name.strip(),
                "ref_code": ref_code.strip(),
                "description": description.strip(),
            })

        return validated
