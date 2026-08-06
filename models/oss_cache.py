import time
from dataclasses import dataclass


@dataclass
class OSSFileCache:
    """OSS 文件缓存数据模型（用于避免重复上传）"""
    id: int                     # 主键ID
    local_path: str             # 本地文件路径
    file_hash: str              # 文件哈希值（SHA256）
    oss_url: str                # OSS URL
    model_name: str             # 关联的模型名称
    uploaded_at: int = 0        # 上传时间（毫秒时间戳）
    expire_at: int = 0          # 过期时间（毫秒时间戳）

    def is_expired(self) -> bool:
        """判断缓存是否已过期"""
        return int(time.time() * 1000) >= self.expire_at
