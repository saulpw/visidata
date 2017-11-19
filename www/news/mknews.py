#!/usr/bin/env python3

import sys
import collections
import os

def htmlize(s):
    return s.replace('\\n', '<br>')

class Column:
    def __init__(self, name, data_col):
        self.name = name
        self.data_col = data_col
        self.href_col = None

def body(newstsv):
    news = list(row[:-1].split('\t') for row in open(newstsv))
    fnext = os.path.split(newstsv)[-1]
    fn, ext = os.path.splitext(fnext)
    table = ''
    table += '<table class="{class_}">\n'.format(class_=fn)
    table += ' <tr>\n'
    cols = collections.OrderedDict()
    for i, header in enumerate(news[0]):
        if header.endswith('_href'):
            colname = header[:-5]
            cols[colname].href_col = i
        else:
            cols[header] = Column(header, i)
            table += ' <th>%s</th>' % header
    table += ' </tr>\n'

    for row in news[1:]:
        table += ' <tr>\n'

        for col in cols.values():
            if col.href_col is not None and row[col.href_col]:
                table += ' <td class="{class_}"><a href="{href}">{content}</a></td>\n'.format(href=row[col.href_col], content=htmlize(row[col.data_col]), class_=col.name.lower())
            else:
                table += ' <td class="{class_}">{content}</td>'.format(class_=col.name.lower(), content=htmlize(row[col.data_col]))

        table += '</tr>\n'

    table += '</table>\n'
    return table

print(body(*sys.argv[1:]))
