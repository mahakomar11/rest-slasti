from datetime import time, datetime
from strict_rfc3339 import validate_rfc3339, rfc3339_to_timestamp
from jsonschema import TypeChecker
from typing import List


def str_to_datetime(t: str) -> datetime:
    """
    Turn string with time in ISO 8601 or RFC 3339
    """
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        return datetime.fromtimestamp(rfc3339_to_timestamp(t))


def parse_intervals(hours: List[str]) -> List[(str, str)]:
    """
    Get intervals in strings, ex. ["10:00-13:00"], return in minutes, [(600, 780)]
    """
    return [_parse_interval(h) for h in hours]


def _parse_interval(interval: str) -> (str, str):
    """
    Parse interval in string, ex. "10:00-13:00", return in minutes, (600, 780)
    """
    start, end = [_str_to_min(t) for t in interval.split('-')]
    if end == 0:
        end = _str_to_min('23:59')
    return start, end


def _str_to_min(raw_t: str) -> int:
    """
    Turn time in string, ex. "10:00", to time in minutes, 600
    """
    t: time = time.fromisoformat(raw_t)
    return t.hour * 60 + t.minute


def is_datetime(checker: TypeChecker, instance) -> bool:
    """
    Function to passed in TypeChecker for checking if property's type is custom type "interval"
    """
    if validate_rfc3339(instance):
        return True
    try:
        datetime.fromisoformat(instance)
    except ValueError:
        return False

    return True


def is_interval(checker: TypeChecker, instance) -> bool:
    """
    Function to passed in TypeChecker for checking if property's type is custom type "datetime"
    """
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

