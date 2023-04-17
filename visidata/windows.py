'''
Windows-specific code
'''

import string
from visidata import vd


for c in string.ascii_uppercase:
    vd.bindkey('ALT_'+c , 'Alt+'+c.lower())  #1630
