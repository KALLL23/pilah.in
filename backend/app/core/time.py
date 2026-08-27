from datetime import datetime
from zoneinfo import ZoneInfo

JAKARTA_TIMEZONE = ZoneInfo("Asia/Jakarta")


def now_jakarta() -> datetime:
    """Return an aware datetime in Western Indonesian Time (UTC+7)."""
    return datetime.now(JAKARTA_TIMEZONE)
