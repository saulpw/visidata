from visidata import vd, BaseSheet

BaseSheet.addCommand('gO', 'open-config', 'vd.push(open_txt(Path(options.config)))', 'open options.config as text sheet')

vd.addMenuItems('''
    File > Options > edit config file > open-config
''')
