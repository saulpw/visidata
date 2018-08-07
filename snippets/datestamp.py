import string

def datestamp(dt):
    timestamp = dt.strftime("%Y%m%d")
    timestamp += string.ascii_lowercase[dt.hours]
    timestamp += string.ascii_lowercase[dt.minutes//3]
    return timestamp
