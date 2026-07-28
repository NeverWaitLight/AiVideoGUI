"""OSS 文件缓存 Repository。"""

import hashlib
from loguru import logger
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from models.oss_cache import OSSFileCache
from storage.orm.models import OSSFileCacheEntity

class OSSFileCacheRepository:
    """OSS 文件缓存数据访问层"""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """
        计算文件哈希（基于路径、修改时间、文件大小）

        Args:
            file_path: 本地文件路径

        Returns:
            SHA256 哈希值

        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat = path.stat()
        # 使用绝对路径 + 修改时间 + 文件大小作为唯一标识
        hash_input = f"{path.resolve()}|{stat.st_mtime}|{stat.st_size}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def get_valid_cache(self, file_path: str, model_name: str) -> Optional[OSSFileCache]:
        """
        获取有效的缓存记录（未过期且文件未变化）

        Args:
            file_path: 本地文件路径
            model_name: 模型名称

        Returns:
            有效的缓存记录，或 None
        """
        try:
            file_hash = self._compute_file_hash(file_path)
        except FileNotFoundError:
            logger.warning(f"文件不存在，无法获取缓存: {file_path}")
            return None

        entity = (
            self.session.query(OSSFileCacheEntity)
            .filter(
                OSSFileCacheEntity.file_hash == file_hash,
                OSSFileCacheEntity.model_name == model_name,
                OSSFileCacheEntity.expire_at > datetime.now(),
            )
            .first()
        )

        if not entity:
            return None

        return OSSFileCache(
            id=entity.id,
            local_path=entity.local_path,
            file_hash=entity.file_hash,
            oss_url=entity.oss_url,
            model_name=entity.model_name,
            uploaded_at=entity.uploaded_at,
            expire_at=entity.expire_at,
        )

    def save_cache(self, file_path: str, model_name: str, oss_url: str) -> OSSFileCache:
        """
        保存新的缓存记录

        Args:
            file_path: 本地文件路径
            model_name: 模型名称
            oss_url: OSS URL

        Returns:
            创建的缓存记录

        Raises:
            FileNotFoundError: 文件不存在
        """
        file_hash = self._compute_file_hash(file_path)
        now = datetime.now()
        expire_at = now + timedelta(hours=48)

        entity = OSSFileCacheEntity(
            local_path=str(Path(file_path).resolve()),
            file_hash=file_hash,
            oss_url=oss_url,
            model_name=model_name,
            uploaded_at=now,
            expire_at=expire_at,
        )

        self.session.add(entity)
        self.session.commit()

        logger.info(f"缓存已保存: {file_path} -> {oss_url} (过期: {expire_at})")

        return OSSFileCache(
            id=entity.id,
            local_path=entity.local_path,
            file_hash=entity.file_hash,
            oss_url=entity.oss_url,
            model_name=entity.model_name,
            uploaded_at=entity.uploaded_at,
            expire_at=entity.expire_at,
        )

    def delete_expired_caches(self) -> int:
        """
        删除所有过期的缓存记录

        Returns:
            删除的记录数
        """
        count = (
            self.session.query(OSSFileCacheEntity)
            .filter(OSSFileCacheEntity.expire_at <= datetime.now())
            .delete()
        )
        self.session.commit()

        if count > 0:
            logger.info(f"已删除 {count} 条过期缓存记录")

        return count

    def delete_cache_by_hash(self, file_hash: str, model_name: str) -> bool:
        """
        删除指定的缓存记录

        Args:
            file_hash: 文件哈希
            model_name: 模型名称

        Returns:
            是否成功删除
        """
        count = (
            self.session.query(OSSFileCacheEntity)
            .filter(
                OSSFileCacheEntity.file_hash == file_hash,
                OSSFileCacheEntity.model_name == model_name,
            )
            .delete()
        )
        self.session.commit()

        return count > 0
