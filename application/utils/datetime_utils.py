from jsonschema import Draft7Validator, TypeChecker, FormatChecker
from jsonschema.validators import extend
import json
from datetime import time, datetime
from strict_rfc3339 import now_to_rfc3339_utcoffset as get_now, validate_rfc3339, rfc3339_to_timestamp


def _str_to_sec(raw_t: str) -> int:
    t: time = time.fromisoformat(raw_t)
    return t.hour * 60 + t.minute


def parse_interval(interval: str) -> (str, str):
    start, end = [_str_to_sec(t) for t in interval.split('-')]
    if end == 0:
        end = _str_to_sec('23:59')
    return start, end


def _is_datetime(checker, instance):
    if validate_rfc3339(instance):
        return True
    try:
        datetime.fromisoformat(instance)
    except ValueError:
        return False

    return True


def _is_interval(checker, instance):
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


def str_to_datetime(t):
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        return datetime.fromtimestamp(rfc3339_to_timestamp(t))

# Create validator extended with custom types 'interval' and 'datetime'
type_checker = Draft7Validator.TYPE_CHECKER.redefine("interval", _is_interval).redefine("datetime", _is_datetime)
ValidatorWithDatetime = extend(Draft7Validator, type_checker=type_checker)

if __name__ == '__main__':
    schema = ValidatorWithDatetime(schema={"title": "schema",
                                           "type": "object",
                                           "properties": {
                                               "working_hours":
                                                   {"type": "interval"},
                                               "assign_time":
                                                   {"type": "datetime"}
                                           }})

    ans = schema.is_valid({'working_hours': '00:10-14:15', "assign_time": "2021-01-10T10:33:01.42Z"})

    time_now = get_now(integer=False)
    # assign_time = "2021-01-10T09:32:14.42Z"
    assign_time = datetime.now()
    complete_time = "2021-01-10T10:33:01.42Z"
    complete_time = datetime.fromtimestamp(rfc3339_to_timestamp(complete_time))

    delta = complete_time - assign_time
    print(time_now)
