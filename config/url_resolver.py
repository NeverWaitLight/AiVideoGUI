from __future__ import annotations

from models.oss_config import OssConfig
from models.provider_config import ProviderConfig


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
