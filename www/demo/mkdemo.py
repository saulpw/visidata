#!/usr/bin/env python3

import sys
import yaml
# step?, command, [additional] input, result
def breakdown(rows):
    ret = '<table class="vd">\n'

    ret += ' <tr>\n'
    ret += '  <th>#</th>'
    ret += '  <th>step</th>'
    ret += '  <th>command</th>'
    ret += '  <th>input</th>'
    ret += '  <th>result</th>'
    ret += ' </tr>\n'

    for i, row in enumerate(rows[1:]):
        colname = '<span class="code">%s</span> column' % row[1]
        ret += ' <tr>\n'
        ret += '  <td class="num">%s</td>' % (i+1)
        ret += '  <td class="step">%s</td>' % (row[5].replace("current column", colname))
        ret += '  <td class="command">%s</td>' %  row[3]
        ret += '  <td class="input">%s</td>' %  row[4]
        ret += '  <td class="screenshot"><img src="%s.png" alt=""/></td>\n' % (i+1)
        ret += ' </tr>\n'

    ret += '</table>'
    return ret


def main(thtml, yamlfn):
    custom = yaml.load(open(yamlfn).read())
    rows = list(row[:-1].split('\t') for row in open(custom['vd']))
    print(open(thtml).read().format(breakdown=breakdown(rows), **custom))

main(*sys.argv[1:])
