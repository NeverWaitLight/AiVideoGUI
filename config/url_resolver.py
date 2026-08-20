from __future__ import annotations

import re

from models.oss_config import OssConfig
from models.provider_config import ProviderConfig

URL_VAR_RE = re.compile(r"\{(\w+):([^}]*)\}")


def has_url_template(url: str) -> bool:
    return bool(url and URL_VAR_RE.search(url))


def extract_url_variable_default(url: str, var_name: str = "base_url") -> str:
    if not url:
        return ""
    for match in URL_VAR_RE.finditer(url):
        if match.group(1) == var_name:
            return match.group(2)
    return ""


def normalize_host(value: str) -> str:
    host = value.strip()
    if not host:
        return ""
    if "://" in host:
        host = host.split("://", 1)[1]
    return host.strip("/")


def resolve_url_template(template: str, variables: dict[str, str | None]) -> str:
    if not template:
        return ""

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)
        user_val = variables.get(var_name)
        if user_val and str(user_val).strip():
            return normalize_host(str(user_val))
        return default

    return URL_VAR_RE.sub(replacer, template)


def get_image_url(cfg: ProviderConfig) -> str:
    return cfg.base_url.rstrip("/") if cfg.base_url else ""


def get_video_submit_url(cfg: ProviderConfig) -> str:
    url = cfg.submit_base_url or cfg.base_url
    return url.rstrip("/") if url else ""


def get_task_base_url(cfg: ProviderConfig) -> str:
    return cfg.task_base_url.rstrip("/") if cfg.task_base_url else ""


def get_chat_base_url(cfg: ProviderConfig) -> str:
    return cfg.base_url.rstrip("/") if cfg.base_url else ""


def get_oss_policy_url(oss: OssConfig) -> str:
    return oss.get_policy_url.rstrip("/") if oss.get_policy_url else ""


def get_oss_policy_params(oss: OssConfig) -> dict[str, str]:
    return dict(oss.get_policy_params)
