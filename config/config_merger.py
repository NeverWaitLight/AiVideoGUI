import json
import os
import shutil
from loguru import logger


class ConfigMerger:
    """配置文件合并工具，启动时将默认配置与用户配置合并"""

    @staticmethod
    def merge_configs(default_config_path: str, user_config_path: str) -> None:
        """
        合并默认配置和用户配置

        策略：
        1. 如果用户配置不存在，直接复制默认配置
        2. 如果用户配置存在：
           - chat_providers: 使用默认配置（保持预设更新）
           - provider_credentials: 保留用户数据
           - active_provider_id: 保留用户选择
           - providers: 保留用户配置（视频、图片等旧配置）
           - app_settings: 保留用户设置
        """
        if not os.path.exists(default_config_path):
            logger.warning(f"默认配置文件不存在：{default_config_path}")
            return

        try:
            with open(default_config_path, encoding="utf-8") as f:
                default_config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"读取默认配置失败：{e}")
            return

        # 用户配置不存在，直接复制
        if not os.path.exists(user_config_path):
            os.makedirs(os.path.dirname(user_config_path), exist_ok=True)
            shutil.copy(default_config_path, user_config_path)
            logger.info(f"首次启动，已复制默认配置到：{user_config_path}")
            return

        # 用户配置存在，合并
        try:
            with open(user_config_path, encoding="utf-8") as f:
                user_config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"读取用户配置失败，将使用默认配置：{e}")
            shutil.copy(default_config_path, user_config_path)
            return

        # 合并策略
        merged_config = default_config.copy()

        # 保留用户的凭证
        if "provider_credentials" in user_config:
            merged_config["provider_credentials"] = user_config["provider_credentials"]

        # 保留用户选择的激活厂商
        if "active_provider_id" in user_config:
            merged_config["active_provider_id"] = user_config["active_provider_id"]

        # 保留旧的 providers 配置
        if "providers" in user_config:
            merged_config["providers"] = user_config["providers"]

        # 保留用户的应用设置
        if "app_settings" in user_config:
            merged_config["app_settings"] = user_config["app_settings"]

        # 确保 provider_credentials 包含所有新增的预设
        if "provider_credentials" not in merged_config:
            merged_config["provider_credentials"] = {}

        for preset in default_config.get("chat_providers", []):
            preset_id = preset["id"]
            if preset_id not in merged_config["provider_credentials"]:
                # 根据类型添加默认凭证结构
                if preset.get("type") == "custom":
                    merged_config["provider_credentials"][preset_id] = {
                        "api_key": "",
                        "base_url": "",
                        "model": "",
                    }
                else:
                    merged_config["provider_credentials"][preset_id] = {"api_key": ""}

        # 保存合并后的配置
        try:
            with open(user_config_path, "w", encoding="utf-8") as f:
                json.dump(merged_config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已合并：{user_config_path}")
        except OSError as e:
            logger.error(f"保存合并后的配置失败：{e}")
