import datetime

def split_list(l, n):
    """
    Divide list into multiple chunks
    :param l: list to divide
    :param n: max length of chunks
    :return: list
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def parse_date(date):
    """
    Return Unix Timestamp from ISO-8601 date string
    :param date:
    :return:
    """
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").timestamp()