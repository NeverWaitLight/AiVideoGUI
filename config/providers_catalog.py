from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


_TASK_MODEL_KEYS: dict[str, tuple[str, ...]] = {
    "image": ("t2i", "i2i", "r2i"),
    "video": ("t2v", "i2v", "r2v"),
}


@dataclass
class ProviderEntry:
    id: str
    name: str
    base_url: str = ""
    models: list[str] = field(default_factory=list)
    task_models: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ProviderTypeCatalog:
    providers: dict[str, ProviderEntry] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)


class ProvidersCatalog:
    """从 settings.json 加载 chat/image/video 可选项、默认 URL 与更新配置。"""

    _VALID_TYPES = ("chat", "image", "video")

    def __init__(self, catalog_path: str | None, fallback_path: str | None = None) -> None:
        self._catalog: dict[str, ProviderTypeCatalog] = {
            t: ProviderTypeCatalog() for t in self._VALID_TYPES
        }
        self._github_repo: str = ""
        self._github_api_url: str = ""
        path = self._resolve_path(catalog_path, fallback_path)
        if path:
            self._load(path)

    @staticmethod
    def _resolve_path(
        catalog_path: str | None, fallback_path: str | None
    ) -> Path | None:
        if catalog_path:
            primary = Path(catalog_path)
            if primary.exists():
                return primary
        if fallback_path:
            fallback = Path(fallback_path)
            if fallback.exists():
                logger.warning(f"工作区 settings.json 不存在，使用内置：{fallback}")
                return fallback
        logger.warning(f"settings.json 不存在：{catalog_path}")
        return None

    @staticmethod
    def _iter_provider_items(providers_data) -> list[tuple[str, dict]]:
        """兼容数组与旧版对象两种 providers 结构。"""
        items: list[tuple[str, dict]] = []
        if isinstance(providers_data, list):
            for item in providers_data:
                if not isinstance(item, dict):
                    continue
                provider_id = str(item.get("id", "")).strip()
                if not provider_id:
                    logger.warning("跳过缺少 id 的 provider 条目")
                    continue
                items.append((provider_id, item))
        elif isinstance(providers_data, dict):
            for name, item in providers_data.items():
                if not isinstance(item, dict):
                    continue
                provider_id = str(item.get("id", name)).strip() or name
                items.append((provider_id, item))
        return items

    @staticmethod
    def _parse_model_list(value) -> list[str]:
        if isinstance(value, list):
            return [str(v) for v in value]
        if value:
            return [str(value)]
        return []

    def _parse_task_models(self, provider_type: str, item: dict) -> dict[str, list[str]]:
        task_models: dict[str, list[str]] = {}
        for task_key in _TASK_MODEL_KEYS.get(provider_type, ()):
            field_name = f"{task_key}_models"
            if field_name in item:
                task_models[task_key] = self._parse_model_list(item.get(field_name))

        # 兼容旧版 model_mappings
        legacy = item.get("model_mappings")
        if isinstance(legacy, dict):
            for task_key, models in legacy.items():
                task_models.setdefault(task_key, self._parse_model_list(models))

        return task_models

    def _load(self, path: Path) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"解析 settings.json 失败：{e}")
            return

        for provider_type in self._VALID_TYPES:
            type_data = data.get(provider_type, {})
            providers_data = type_data.get("providers", [])
            entries: dict[str, ProviderEntry] = {}
            order: list[str] = []
            for provider_id, item in self._iter_provider_items(providers_data):
                if provider_id in entries:
                    logger.warning(
                        f"重复的 provider id 已忽略：type={provider_type}, id={provider_id}"
                    )
                    continue
                name = str(item.get("name", "")).strip() or provider_id
                entries[provider_id] = ProviderEntry(
                    id=provider_id,
                    name=name,
                    base_url=item.get("base_url", ""),
                    models=self._parse_model_list(item.get("models", [])),
                    task_models=self._parse_task_models(provider_type, item),
                )
                order.append(provider_id)
            self._catalog[provider_type] = ProviderTypeCatalog(
                providers=entries, order=order
            )

        update = data.get("update", {})
        if isinstance(update, dict):
            self._github_repo = str(update.get("github_repo", "") or "").strip()
            self._github_api_url = str(update.get("github_api_url", "") or "").strip()

        logger.info(
            "settings.json 已加载："
            + ", ".join(
                f"{t}={self._catalog[t].order}"
                for t in self._VALID_TYPES
            )
        )

    def _get_entry(self, provider_type: str, provider_id: str) -> ProviderEntry | None:
        if provider_type not in self._catalog:
            return None
        return self._catalog[provider_type].providers.get(provider_id)

    def list_providers(self, provider_type: str) -> list[dict[str, str]]:
        """返回 [{id, name}, ...] 供设置页展示。"""
        if provider_type not in self._catalog:
            return []
        type_catalog = self._catalog[provider_type]
        result: list[dict[str, str]] = []
        for provider_id in type_catalog.order:
            entry = type_catalog.providers[provider_id]
            result.append({"id": entry.id, "name": entry.name})
        return result

    def list_provider_ids(self, provider_type: str) -> list[str]:
        if provider_type not in self._catalog:
            return []
        return list(self._catalog[provider_type].order)

    def get_name(self, provider_type: str, provider_id: str) -> str:
        entry = self._get_entry(provider_type, provider_id)
        return entry.name if entry else ""

    def get_base_url(self, provider_type: str, provider_id: str) -> str:
        entry = self._get_entry(provider_type, provider_id)
        return entry.base_url if entry else ""

    def list_models(self, provider_type: str, provider_id: str) -> list[str]:
        """chat 等扁平 models 列表。"""
        entry = self._get_entry(provider_type, provider_id)
        if not entry:
            return []
        return list(entry.models)

    def list_models_for_task(
        self, provider_type: str, provider_id: str, task_type: str
    ) -> list[str]:
        """按任务类型读取 {task}_models，例如 t2v_models / t2i_models。"""
        entry = self._get_entry(provider_type, provider_id)
        if not entry:
            return []
        if task_type in entry.task_models:
            return list(entry.task_models[task_type])
        return list(entry.models)

    def get_update_github_repo(self) -> str:
        return self._github_repo

    def get_update_github_api_url(self) -> str:
        return self._github_api_url
