import os
import re
import csv
import time


class CsvReader(object):
    """
    Wrapper around csv reader that ignores non utf-8 chars
    and strips the record
    """
    def __init__(self, filename, delimiter=','):
        self.reader = csv.reader(open(filename, 'rbU'), delimiter=delimiter)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next() 

    def next(self):
        row = next(self.reader)
        row = [el.decode('utf8', errors='ignore').replace('\"', '').strip()
               for el in row]
        return row


# Fast way to determine line count
def count_lines(filename, max=None):
    f = open(filename)
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.read  # loop optimization

    buf = read_f(buf_size)
    while buf:
        lines += buf.count('\n')
        if max is not None and lines >= max:
            return max
        buf = read_f(buf_size)
    return lines

title_case = lambda text: " ".join([x.capitalize() for x in text.split(" ")])


# converts "JohnDoe" to "John Doe"
def uncamel(text):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', text)
    s1 = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
    return s1.replace('  ', ' ')


def local_tz_offset():
    # http://stackoverflow.com/questions/1111056/get-tz-information-of-the-system-in-python
    return (time.timezone if (time.localtime().tm_isdst == 0)
                          else time.altzone) / 60 / 60 * -1
