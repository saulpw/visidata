from visidata import Sheet


Sheet.addCommand('', 'clean-names', '''
options.clean_names = True;
for c in visibleCols:
    c.name = c.name
''', 'set options.clean_names on sheet and clean visible column names')
