from visidata import *

command(['KEY_F(1)', 'z?'], 'vd.push(HelpSheet(name + "_commands", *sheet.commands.maps))', 'open command help sheet')

## Built-in sheets
class HelpSheet(Sheet):
    'Help sheet, showing keystrokes etc. from given source(s).'

    def reload(self):
        'Populate sheet via `reload` function.'
        self.rows = []
        for i, src in enumerate(self.sources):
            self.rows.extend((i, v) for v in src.values())
        self.columns = [SubrowColumn(ColumnItem('keystrokes', 0), 1),
                        SubrowColumn(ColumnItem('action', 1), 1),
                        Column('with_g_prefix', str, lambda r,self=self: self.sources[r[0]].get('g' + r[1][0], (None,'-'))[1]),
                        SubrowColumn(ColumnItem('execstr', 2, width=0), 1)
                ]
        self.nKeys = 1

status('<F1> or z? opens help')
