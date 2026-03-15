import re

import visidata
from visidata import vd, VisiData, BaseSheet, Sheet, Column, AttrColumn, CellColorizer, Option


@BaseSheet.lazy_property
def optionsSheet(sheet):
    return OptionsSheet(sheet.name+"_options", source=sheet)

@VisiData.lazy_property
def globalOptionsSheet(vd):
    return OptionsSheet('global_options', source='global')


@VisiData.api
class OptionsSheet(Sheet):
    _rowtype = Option  # rowdef: Option
    rowtype = 'options'
    precious = False
    columns = (
        Column('option', getter=lambda col,row: row.name),
        Column('module', getter=lambda col,row: row.module, disp_expert=1),
        Column('value',
            getter=lambda col,row: col.sheet.diffOption(row.name),
            setter=lambda col,row,val: vd.options.set(row.name, val, col.sheet.source)
            ),
        Column('default', getter=lambda col,row: vd.options.getdefault(row.name)),
        Column('description', width=40, getter=lambda col,row: vd.options._get(row.name, 'default').helpstr),
        AttrColumn('replayable', disp_expert=1),
    )
    colorizers = [
        CellColorizer(3, None, lambda s,c,r,v: v.value if r and c in s.columns[2:4] and r.name.startswith('color_') else None),
    ]
    nKeys = 2

    @property
    def guide(self):
        if self.source == 'global':
            r = '# Global Options\nThis is a list of global option settings.'
        else:
            r = '# Sheet Options\nThis is a list of option settings specifically for the current sheet.'

        r += f'\n\n- `e` to edit/toggle the current option value'
        r += '\n- `d` to restore option to builtin default'
        r += '\n- `z Ctrl+S` to save option overrides to config file'
        return r

    def diffOption(self, optname):
        return vd.options.getonly(optname, self.source, '')

    def editOption(self, row):
        currentValue = vd.options.getobj(row.name, self.source)
        vd.addUndo(vd.options.set, row.name, currentValue, self.source)
        if isinstance(row.value, bool):
            vd.options.set(row.name, not currentValue, self.source)
        else:
            helpstr = f'# options.{self.cursorRow.name}'
            opt = vd.options._get(self.cursorRow.name, 'default')
            if opt.helpstr:
                x = getattr(vd, 'help_'+opt.helpstr, opt.helpstr or '')
                helpstr += (x or '').strip()
            if opt.extrahelp:
                helpstr += '\n'+opt.extrahelp.strip()
            valcolidx = self.visibleCols.index(self.column(self.valueColName))
            v = self.editCell(valcolidx, value=currentValue, help=helpstr)
            vd.options.set(row.name, v, self.source)

    @property
    def valueColName(self):
        return 'global_value' if self.source == 'global' else 'sheet_value'

    def beforeLoad(self):
        super().beforeLoad()
        self.columns[2].name = self.valueColName

    def iterload(self):
        for k in vd.options.keys():
            v = vd.options._get(k)
            if v.cli_only:
                continue
            if v.sheettype in [None, BaseSheet]:
                yield v
            elif self.source != 'global' and v.sheettype in self.source.superclasses():
                yield v

    def newRow(self):
        vd.fail('adding rows to the options sheet is not supported.')


BaseSheet.addCommand('O', 'options-global', 'vd.push(vd.globalOptionsSheet)', 'open Options Sheet: edit global options (apply to all sheets)')

BaseSheet.addCommand('zO', 'options-sheet', 'vd.push(sheet.optionsSheet)', 'open Options Sheet: edit sheet options (apply to current sheet only)')

@OptionsSheet.api
def commit(sheet, *rows):
    'Save option overrides to config file.'
    p = visidata.Path(vd.options.config)
    configlines = [re.sub(r'\s*=\s*', '=', L, count=1) for L in p] if p.exists() else []

    newlines = []
    for row in sheet.rows:
        val = sheet.diffOption(row.name)
        if val != '' and val != vd.options.getdefault(row.name):
            line = f'options.{row.name}={repr(val)}'
            if line not in configlines:
                newlines.append(line)

    if not newlines:
        vd.fail('no new options to save')

    vd.confirm(f'save {len(newlines)} options to {p}? ')

    with open(str(p), mode='a') as fp:
        for line in newlines:
            print(line, file=fp)

    vd.status(f'saved {len(newlines)} options to {p}')


OptionsSheet.addCommand('zCtrl+S', 'commit-sheet', 'commit()', 'save option overrides to config file')
OptionsSheet.addCommand('d', 'unset-option', 'options.unset(cursorRow.name, str(source))', 'remove option override for this context')
OptionsSheet.addCommand(None, 'edit-option', 'editOption(cursorRow)', 'edit option at current row')
OptionsSheet.bindkey('e', 'edit-option')
OptionsSheet.bindkey('Enter', 'edit-option')

vd.addMenuItems('''
    File > Options > all sheets > options-global
    File > Options > this sheet > options-sheet
''')
