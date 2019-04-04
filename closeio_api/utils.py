import time


def local_tz_offset():
    # http://stackoverflow.com/questions/1111056/get-tz-information-of-the-system-in-python
    return (time.timezone if (time.localtime().tm_isdst == 0)
                          else time.altzone) / 60 / 60 * -1
