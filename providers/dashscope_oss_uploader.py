from loguru import logger
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

@dataclass
class DashScopeUploadPolicy:

    policy: str
    signature: str
    upload_dir: str
    upload_host: str
    expire_in_seconds: int
    max_file_size_mb: int
    oss_access_key_id: str
    x_oss_object_acl: str
    x_oss_forbid_overwrite: str

    @property
    def expire_time(self) -> datetime:
        return datetime.now() + timedelta(seconds=self.expire_in_seconds)

class DashScopeOSSUploader:

    def __init__(self, api_key: str, base_url: str):
        if not base_url:
            raise ValueError("DashScope OSS 上传需要配置 base_url")
        self.api_key = api_key
        self._policy_api_url = f"{base_url.rstrip('/')}/uploads"

    def get_upload_policy(self, model_name: str) -> DashScopeUploadPolicy:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        params = {"action": "getPolicy", "model": model_name}

        logger.debug(f"获取上传凭证: model={model_name}")

        try:
            response = requests.get(
                self._policy_api_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"获取上传凭证失败: {e}")
            raise RuntimeError(f"获取上传凭证失败: {e}") from e

        data = response.json().get("data", {})
        policy = DashScopeUploadPolicy(
            policy=data["policy"],
            signature=data["signature"],
            upload_dir=data["upload_dir"],
            upload_host=data["upload_host"],
            expire_in_seconds=data["expire_in_seconds"],
            max_file_size_mb=data["max_file_size_mb"],
            oss_access_key_id=data["oss_access_key_id"],
            x_oss_object_acl=data["x_oss_object_acl"],
            x_oss_forbid_overwrite=data["x_oss_forbid_overwrite"],
        )

        logger.debug(
            f"凭证获取成功，有效期 {policy.expire_in_seconds} 秒，过期时间: {policy.expire_time}"
        )
        return policy

    def upload_file_to_oss(self, policy: DashScopeUploadPolicy, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_name = path.name
        key = f"{policy.upload_dir}/{file_name}"

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > policy.max_file_size_mb:
            raise RuntimeError(
                f"文件大小 {file_size_mb:.2f}MB 超过限制 {policy.max_file_size_mb}MB"
            )

        logger.debug(f"上传文件: {file_name} ({file_size_mb:.2f}MB) -> {key}")

        with open(file_path, "rb") as file:
            files = {
                "OSSAccessKeyId": (None, policy.oss_access_key_id),
                "Signature": (None, policy.signature),
                "policy": (None, policy.policy),
                "x-oss-object-acl": (None, policy.x_oss_object_acl),
                "x-oss-forbid-overwrite": (None, policy.x_oss_forbid_overwrite),
                "key": (None, key),
                "success_action_status": (None, "200"),
                "file": (file_name, file),
            }

            try:
                response = requests.post(policy.upload_host, files=files, timeout=60)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"上传文件失败: {e}")
                raise RuntimeError(f"上传文件失败: {e}") from e

        oss_url = f"oss://{key}"
        logger.info(f"文件上传成功: {oss_url}")
        return oss_url

    def upload(self, file_path: str, model_name: str) -> tuple[str, datetime]:
        policy = self.get_upload_policy(model_name=model_name)

        oss_url = self.upload_file_to_oss(policy=policy, file_path=file_path)

        expire_time = datetime.now() + timedelta(hours=48)

        logger.info(f"文件上传完成，有效期至 {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return oss_url, expire_time

def upload_file(
    api_key: str, model_name: str, file_path: str, base_url: str
) -> tuple[str, datetime]:
    uploader = DashScopeOSSUploader(api_key, base_url=base_url)
    return uploader.upload(file_path=file_path, model_name=model_name)
