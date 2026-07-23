"""时间戳工具函数。"""

import time
from datetime import datetime


def now_ms() -> int:
    """
    获取当前 13 位毫秒时间戳。

    Returns:
        int: 当前时间的毫秒时间戳

    Example:
        >>> ts = now_ms()
        >>> ts
        1721721600000
    """
    return int(time.time() * 1000)


def ms_to_datetime(ms: int) -> datetime:
    """
    将毫秒时间戳转换为 datetime 对象（用于 UI 显示）。

    Args:
        ms: 13 位毫秒时间戳

    Returns:
        datetime: 对应的 datetime 对象

    Example:
        >>> dt = ms_to_datetime(1721721600000)
        >>> dt.year
        2024
    """
    return datetime.fromtimestamp(ms / 1000.0)


def format_time(ms: int) -> str:
    """
    将毫秒时间戳格式化为 UI 显示时间。

    今天显示 HH:MM，其他日期显示 MM-DD HH:MM。

    Args:
        ms: 13 位毫秒时间戳

    Returns:
        格式化后的时间字符串
    """
    dt = ms_to_datetime(ms)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")
