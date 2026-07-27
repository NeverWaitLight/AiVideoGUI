"""OSS 文件缓存数据模型。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OSSFileCache:
    """OSS 文件缓存记录"""

    id: int
    local_path: str
    file_hash: str
    oss_url: str
    model_name: str
    uploaded_at: datetime
    expire_at: datetime

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return datetime.now() >= self.expire_at
