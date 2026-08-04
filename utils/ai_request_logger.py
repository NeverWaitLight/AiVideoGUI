import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from config.manager import ConfigManager


class AIRequestLogger:
    """
    AI 请求日志记录器

    按项目和模块分类记录所有 AI 调用的请求和响应，生成结构化的 Markdown 日志文件。

    功能特性：
    - 按项目组织日志文件夹（logs/{项目名称}_{项目ID}/）
    - 按模块分类（outline.md, script.md, character.md, storyboard.md）
    - 全局日志（logs/global.md）用于无项目关联的调用
    - 自动转换文件路径为相对路径
    - 线程安全（基于 loguru 的 enqueue=True）
    """

    def __init__(self, config_manager: ConfigManager, workspace_root: str) -> None:
        self._config = config_manager
        self._workspace_root = Path(workspace_root)
        self._logs_root = self._workspace_root / "logs"

    def log_request(
        self,
        request_type: str,
        module: str,
        payload: dict[str, Any],
        response: dict[str, Any] | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        context: str | None = None,
    ) -> None:
        """
        记录 AI 请求到对应的日志文件

        Args:
            request_type: 请求类型（如 "text_generation", "image_generation", "video_generation"）
            module: 模块名称（"outline", "script", "character", "storyboard"）
            payload: 请求体字典
            response: 响应体字典（可选）
            project_id: 项目 ID（必需）
            project_name: 项目名称（必需）
            context: 额外上下文信息（如 "大纲优化"）
        """
        if not self._config.settings.enable_ai_request_logging:
            return

        # 项目信息是必需的，如果缺失则记录错误但不抛出异常
        if project_id is None or project_name is None:
            logger.warning(
                f"AI 请求日志缺少项目信息，跳过记录: module={module}, context={context}"
            )
            return

        try:
            log_file_path = self._get_log_file_path(project_id, project_name, module)

            sanitized_payload = self._sanitize_payload(payload)
            sanitized_response = self._sanitize_response(response) if response else None

            payload_with_relative_paths = self._convert_paths_to_relative(
                sanitized_payload, log_file_path
            )

            log_entry = self._format_log_entry(
                request_type=request_type,
                context=context or module,
                payload=payload_with_relative_paths,
                response=sanitized_response,
            )

            self._append_to_file(log_file_path, log_entry)

            logger.debug(
                f"AI 请求日志已记录: project_id={project_id}, module={module}, file={log_file_path}"
            )
        except Exception as e:
            logger.exception(f"记录 AI 请求日志失败: {e}")

    def _get_log_file_path(
        self, project_id: int, project_name: str, module: str
    ) -> Path:
        """获取日志文件路径"""
        safe_project_name = self._sanitize_filename(project_name)
        project_folder = self._logs_root / f"{safe_project_name}_{project_id}"
        project_folder.mkdir(parents=True, exist_ok=True)
        log_file = project_folder / f"{module}.md"
        return log_file

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的特殊字符"""
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.strip()
        if not filename:
            filename = "unnamed"
        return filename

    def _sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """移除请求体中的敏感信息（如 Authorization header）"""
        sanitized = payload.copy()

        if "headers" in sanitized:
            headers = sanitized["headers"].copy()
            if "Authorization" in headers:
                headers["Authorization"] = "Bearer [REDACTED]"
            sanitized["headers"] = headers

        return sanitized

    def _sanitize_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """清理响应体（当前无需处理，响应不包含敏感信息）"""
        return response

    def _convert_paths_to_relative(
        self, data: Any, log_file_path: Path
    ) -> Any:
        """递归转换数据中的绝对路径为相对路径"""
        if isinstance(data, dict):
            return {
                k: self._convert_paths_to_relative(v, log_file_path)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._convert_paths_to_relative(item, log_file_path) for item in data]
        elif isinstance(data, str):
            return self._try_convert_path(data, log_file_path)
        else:
            return data

    def _try_convert_path(self, text: str, log_file_path: Path) -> str:
        """尝试将字符串中的绝对路径转换为相对路径"""
        try:
            path = Path(text)
            if path.is_absolute() and path.exists():
                log_dir = log_file_path.parent
                relative_path = os.path.relpath(path, log_dir)
                return relative_path.replace("\\", "/")
        except (ValueError, OSError):
            pass

        return text

    def _format_log_entry(
        self,
        request_type: str,
        context: str,
        payload: dict[str, Any],
        response: dict[str, Any] | None = None,
    ) -> str:
        """格式化日志条目为 Markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            f"## {timestamp} - {context}",
            "",
            f"**操作类型**: {request_type}",
            "",
            "**请求详情**:",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ]

        if response:
            lines.extend([
                "**响应详情**:",
                "```json",
                json.dumps(response, ensure_ascii=False, indent=2),
                "```",
                "",
            ])

        lines.extend([
            "---",
            "",
        ])

        return "\n".join(lines)

    def _append_to_file(self, file_path: Path, content: str) -> None:
        """追加内容到文件（线程安全）"""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)
