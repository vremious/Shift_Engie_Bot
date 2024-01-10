import re


def input_date(date):
    pattern = r'[,;|./ ]'
    date_splitted = (re.split(pattern, str(date)))
    day = date_splitted[0]
    month = date_splitted[1]
    year = date_splitted[2]
    return f'{day}.{month}.{year}'
