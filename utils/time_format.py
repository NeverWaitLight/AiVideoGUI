"""时间格式化工具。"""

from datetime import datetime


def timestamp_to_datetime(timestamp: int) -> datetime:
    """将13位时间戳（毫秒）转换为 datetime 对象。

    Args:
        timestamp: 13位时间戳（毫秒）

    Returns:
        datetime 对象
    """
    return datetime.fromtimestamp(timestamp / 1000)


def format_timestamp(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """将13位时间戳（毫秒）格式化为字符串。

    Args:
        timestamp: 13位时间戳（毫秒）
        fmt: 格式化字符串

    Returns:
        格式化后的时间字符串
    """
    dt = timestamp_to_datetime(timestamp)
    return dt.strftime(fmt)


def format_timestamp_short(timestamp: int) -> str:
    """将13位时间戳（毫秒）格式化为简短字符串（今天显示时分，其他显示月日时分）。

    Args:
        timestamp: 13位时间戳（毫秒）

    Returns:
        格式化后的时间字符串
    """
    dt = timestamp_to_datetime(timestamp)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")
