from datetime import time


def _str_to_sec(raw_t: str) -> int:
    t: time = time.fromisoformat(raw_t)
    return t.hour * 60 + t.minute


def parse_interval(interval: str) -> (str, str):
    start, end = [_str_to_sec(t) for t in interval.split('-')]
    return start, end


# def parse_intervals(hours: list[str]) -> list:
#     return [parse_interval(wh) for wh in hours]

