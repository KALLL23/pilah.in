from datetime import timedelta

from app.core.time import now_jakarta


def test_jakarta_time_is_timezone_aware_utc_plus_seven() -> None:
    current = now_jakarta()
    assert current.tzinfo is not None
    assert current.utcoffset() == timedelta(hours=7)
