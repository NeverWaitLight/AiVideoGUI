import hashlib
from loguru import logger
import os
import time
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from models.oss_cache import OSSFileCache
from storage.orm.oss_cache_entity import OSSFileCacheEntity

class OSSFileCacheRepository:

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat = path.stat()
        hash_input = f"{path.resolve()}|{stat.st_mtime}|{stat.st_size}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def get_valid_cache(self, file_path: str, model_name: str) -> Optional[OSSFileCache]:
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
                OSSFileCacheEntity.expire_at > int(time.time() * 1000),
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
        file_hash = self._compute_file_hash(file_path)
        now = int(time.time() * 1000)
        expire_at = now + 48 * 60 * 60 * 1000

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
        count = (
            self.session.query(OSSFileCacheEntity)
            .filter(OSSFileCacheEntity.expire_at <= int(time.time() * 1000))
            .delete()
        )
        self.session.commit()

        if count > 0:
            logger.info(f"已删除 {count} 条过期缓存记录")

        return count

    def delete_cache_by_hash(self, file_hash: str, model_name: str) -> bool:
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
