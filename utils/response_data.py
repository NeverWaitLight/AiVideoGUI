from __future__ import annotations

import json
import os
import time
from pathlib import PurePosixPath
from typing import Any

from utils.path_converter import to_relative_path

_BINARY_CONTENT_PREFIXES = (
    "image/",
    "video/",
    "audio/",
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/gzip",
)


def _extension_from_content_type(content_type: str) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "application/gzip": ".gz",
        "application/octet-stream": ".bin",
    }
    return mapping.get(ct, ".bin")


def _is_binary_content_type(content_type: str) -> bool:
    ct = (content_type or "").split(";")[0].strip().lower()
    if not ct:
        return False
    return any(ct.startswith(prefix) or ct == prefix.rstrip("/") for prefix in _BINARY_CONTENT_PREFIXES)


def _write_bytes_to_workspace(
    data: bytes,
    *,
    workspace_root: str,
    task_id: int,
    content_type: str = "",
) -> str:
    ext = _extension_from_content_type(content_type)
    relative = str(
        PurePosixPath("task_responses") / f"{task_id}_{int(time.time() * 1000)}{ext}"
    )
    absolute = os.path.join(workspace_root, relative.replace("/", os.sep))
    os.makedirs(os.path.dirname(absolute), exist_ok=True)
    with open(absolute, "wb") as f:
        f.write(data)
    return to_relative_path(absolute, workspace_root)


def normalize_response_data(
    raw: Any,
    *,
    workspace_root: str,
    task_id: int,
    content_type: str = "",
) -> str:
    """将 HTTP 响应规范化为可入库的字符串。

    文本/JSON 直接返回字符串；字节流写入工作区后返回相对路径。
    """
    if raw is None:
        return ""

    if hasattr(raw, "content") and hasattr(raw, "headers") and hasattr(raw, "text"):
        resp_content_type = content_type or raw.headers.get("Content-Type", "")
        if _is_binary_content_type(resp_content_type):
            return _write_bytes_to_workspace(
                raw.content,
                workspace_root=workspace_root,
                task_id=task_id,
                content_type=resp_content_type,
            )
        try:
            text = raw.text
        except Exception:
            return _write_bytes_to_workspace(
                raw.content,
                workspace_root=workspace_root,
                task_id=task_id,
                content_type=resp_content_type,
            )
        return text if text is not None else ""

    if isinstance(raw, (bytes, bytearray)):
        return _write_bytes_to_workspace(
            bytes(raw),
            workspace_root=workspace_root,
            task_id=task_id,
            content_type=content_type,
        )

    if isinstance(raw, (dict, list)):
        return json.dumps(raw, ensure_ascii=False)

    if isinstance(raw, str):
        return raw

    return str(raw)
