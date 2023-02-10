'''
Load new table from system clipboard
'''

from visidata import vd, BaseSheet, Path


@BaseSheet.api
def open_syspaste(sheet, filetype='tsv'):
    import io

    v = vd.sysclipValue().strip() or vd.fail('nothing to open')

    p = Path('syspaste'+'.'+filetype, fp=io.BytesIO(v.encode('utf-8')))
    return vd.openSource(p, filetype=filetype)


BaseSheet.addCommand('gShift+P', 'open-syspaste', 'vd.push(open_syspaste(filetype=vd.input("paste as filetype: ", value="tsv")))', 'open clipboard as filetype')
