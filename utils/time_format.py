from datetime import datetime


def timestamp_to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000)


def format_timestamp(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    dt = timestamp_to_datetime(timestamp)
    return dt.strftime(fmt)


def format_timestamp_short(timestamp: int) -> str:
    dt = timestamp_to_datetime(timestamp)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")
