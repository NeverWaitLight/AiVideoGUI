import time
from dataclasses import dataclass


@dataclass
class OSSFileCache:
    id: int
    local_path: str
    file_hash: str
    oss_url: str
    model_name: str
    uploaded_at: int = 0
    expire_at: int = 0

    def is_expired(self) -> bool:
        return int(time.time() * 1000) >= self.expire_at
