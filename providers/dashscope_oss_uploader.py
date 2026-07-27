"""
阿里云 DashScope 临时存储文件上传模块

提供文件上传到阿里云 DashScope 临时存储空间的功能，生成有效期为 48 小时的 oss:// URL。
适用于视频生成、图片生成等需要传入文件 URL 的场景。

使用限制：
- 文件大小不超过 1GB
- 文件有效期 48 小时
- 文件与模型绑定，需指定模型名称
- 文件与主账号绑定，API Key 必须一致
- 上传凭证接口限流 100 QPS（按主账号+模型维度）

References:
- https://www.alibabacloud.com/help/zh/model-studio/get-temporary-file-url
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class DashScopeUploadPolicy:
    """文件上传凭证"""

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
        """凭证过期时间"""
        return datetime.now() + timedelta(seconds=self.expire_in_seconds)


class DashScopeOSSUploader:
    """阿里云 DashScope 临时存储文件上传器"""

    POLICY_API_URL = "https://dashscope.aliyuncs.com/api/v1/uploads"

    def __init__(self, api_key: str):
        """
        初始化上传器

        Args:
            api_key: 阿里云 DashScope API Key
        """
        self.api_key = api_key

    def get_upload_policy(self, model_name: str) -> DashScopeUploadPolicy:
        """
        获取文件上传凭证

        Args:
            model_name: 模型名称（如 qwen-vl-plus, wan2.7-t2v）

        Returns:
            上传凭证对象

        Raises:
            RuntimeError: 获取凭证失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        params = {"action": "getPolicy", "model": model_name}

        logger.debug(f"获取上传凭证: model={model_name}")

        try:
            response = requests.get(
                self.POLICY_API_URL, headers=headers, params=params, timeout=10
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
        """
        上传文件到临时存储空间

        Args:
            policy: 上传凭证
            file_path: 本地文件路径

        Returns:
            oss:// 前缀的文件 URL（有效期 48 小时）

        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: 上传失败
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_name = path.name
        key = f"{policy.upload_dir}/{file_name}"

        # 检查文件大小
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
        """
        上传文件并返回临时 URL（一站式接口）

        Args:
            file_path: 本地文件路径
            model_name: 模型名称（如 qwen-vl-plus, wan2.7-t2v）

        Returns:
            (oss_url, expire_time) - 临时 URL 和过期时间

        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: 上传失败
        """
        # 1. 获取上传凭证
        policy = self.get_upload_policy(model_name)

        # 2. 上传文件
        oss_url = self.upload_file_to_oss(policy, file_path)

        # 3. 计算文件过期时间（48 小时）
        expire_time = datetime.now() + timedelta(hours=48)

        logger.info(f"文件上传完成，有效期至 {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return oss_url, expire_time


def upload_file(
    api_key: str, model_name: str, file_path: str
) -> tuple[str, datetime]:
    """
    快捷函数：上传文件到阿里云 DashScope 临时存储

    Args:
        api_key: 阿里云 DashScope API Key
        model_name: 模型名称（如 qwen-vl-plus, wan2.7-t2v）
        file_path: 本地文件路径

    Returns:
        (oss_url, expire_time) - 临时 URL 和过期时间

    Raises:
        FileNotFoundError: 文件不存在
        RuntimeError: 上传失败

    Example:
        >>> api_key = os.getenv("DASHSCOPE_API_KEY")
        >>> oss_url, expire_time = upload_file(api_key, "wan2.7-t2v", "video.mp4")
        >>> print(f"URL: {oss_url}, 过期: {expire_time}")
    """
    uploader = DashScopeOSSUploader(api_key)
    return uploader.upload(file_path, model_name)
