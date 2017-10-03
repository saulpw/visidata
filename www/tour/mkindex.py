#!/usr/bin/env python3

# Usage: $0 <*.yaml>

import sys
import yaml

def body():
#    index = '<div id="index_container">\n'
    index = ''
    index += '<table class="index_list">\n'

    # <li><a href='tour_url'>Tour Name</a></li>\n
    for fnyaml in sys.argv[1:]:
        tour = yaml.load(open(fnyaml).read())
        index += '<tr>'
        index += '<td><a href="{tour_url}">{tour_title}</a></td>\n'.format(tour_url=tour['name'], tour_title=tour['name'])
        index += '<td>{workflow}</td>\n'.format(workflow=tour.get('workflow', ''))
        index += '</tr>'
    index += '</table>\n'
#    index += '</div>\n'
    return index

print(body())
