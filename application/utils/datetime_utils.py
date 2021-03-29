from datetime import time, datetime
from strict_rfc3339 import validate_rfc3339, rfc3339_to_timestamp


def str_to_datetime(t):
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        return datetime.fromtimestamp(rfc3339_to_timestamp(t))


def parse_intervals(hours: list[str]) -> list[(str, str)]:
    return [_parse_interval(h) for h in hours]


def _parse_interval(interval: str) -> (str, str):
    start, end = [_str_to_sec(t) for t in interval.split('-')]
    if end == 0:
        end = _str_to_sec('23:59')
    return start, end


def _str_to_sec(raw_t: str) -> int:
    t: time = time.fromisoformat(raw_t)
    return t.hour * 60 + t.minute


def is_datetime(checker, instance):
    if validate_rfc3339(instance):
        return True
    try:
        datetime.fromisoformat(instance)
    except ValueError:
        return False

    return True


def is_interval(checker, instance):
    if not isinstance(instance, str):
        return False
    elif '-' not in instance:
        return False

    times = instance.split('-')
    if len(times) != 2:
        return False

    try:
        time.fromisoformat(times[0])
        time.fromisoformat(times[1])
    except ValueError:
        return False

    return True

