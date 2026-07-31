from datetime import datetime


def format_timestamp(timestamp_ms: int) -> str:
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_timestamp_ms() -> int:
    import time
    return int(time.time() * 1000)
