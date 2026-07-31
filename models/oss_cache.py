from dataclasses import dataclass
from datetime import datetime


@dataclass
class OSSFileCache:
    id: int
    local_path: str
    file_hash: str
    oss_url: str
    model_name: str
    uploaded_at: datetime
    expire_at: datetime

    def is_expired(self) -> bool:
        return datetime.now() >= self.expire_at
