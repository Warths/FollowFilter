import datetime


def warning(text):
    """
    Red bold log
    :param text: str
    """
    print('\033[1;31m', get_date(), text, '\033[0m', sep='')


def notice(text):
    """
    Yellow log
    :param text: str
    """
    print('\033[33m', get_date(), text, '\033[0m', sep='')


def log(text):
    """
    Blue log
    :param text: str
    """
    print('\033[34m', get_date(), text, '\033[0m', sep='')


def discrete(text):
    """
    Dark cyan log
    :param text: str
    """
    print('\033[90m', get_date(), text, '\033[0m', sep='')


def get_date():
    """
    Format a readable timestamp
    :return: str
    """
    return datetime.datetime.now().strftime("[%d/%m/%y - %H:%M:%S.%f] - ")
