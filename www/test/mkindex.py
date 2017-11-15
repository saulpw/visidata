#!/usr/bin/env python3

# Usage: $0 <*.yaml>

import sys
import yaml

def body():
#    index = '<div id="index_container">\n'
    index = ''
    index += '<table class="index_list">\n'

    # <li><a href='test_url'>test Name</a></li>\n
    for fnyaml in sys.argv[1:]:
        test = yaml.load(open(fnyaml).read())
        index += '<tr>'
        index += '<td><a href="{test_url}">{test_title}</a></td>\n'.format(test_url=test['name'], test_title=test['name'])
        index += '<td>{workflow}</td>\n'.format(workflow=test.get('question', ''))
        index += '</tr>'
    index += '</table>\n'
#    index += '</div>\n'
    return index

print(body())
