"""时间戳格式化工具。"""

from datetime import datetime


def format_timestamp(timestamp_ms: int) -> str:
    """
    将 13 位时间戳（毫秒）格式化为可读字符串。

    Args:
        timestamp_ms: 13 位时间戳（毫秒）

    Returns:
        格式化后的时间字符串（如 "2024-01-15 14:30:45"）
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_timestamp_ms() -> int:
    """
    获取当前时间的 13 位时间戳（毫秒）。

    Returns:
        当前时间的毫秒时间戳
    """
    import time
    return int(time.time() * 1000)
