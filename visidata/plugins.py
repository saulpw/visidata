import os.path
import os
import sys
import re
import shutil
import importlib
import subprocess
import urllib.error

from visidata import VisiData, vd, Path, CellColorizer, Sheet, AttrDict, ItemColumn, Column, Progress, ExpectedException, BaseSheet, asyncthread


vd.option('plugins_autoload', True, 'do not autoload plugins if False')


@VisiData.property
def pluginConfig(self):
    return Path(os.path.join(vd.options.visidata_dir, "plugins", "__init__.py"))


@VisiData.property
def pluginConfigLines(self):
    return Path(self.pluginConfig).open(mode='r', encoding='utf-8').readlines()

def _plugin_import_name(self, plugin):
    if not plugin.url:
        return 'visidata.plugins.'+plugin.name
    if 'git+' in plugin.url:
        return plugin.name
    return "plugins."+plugin.name


@VisiData.api
def enablePlugin(vd, plugin:str):
    with vd.pluginConfig.open(mode='a', encoding='utf-8') as fprc:
        print(f'import {plugin}', file=fprc)
        importlib.import_module(plugin)
        vd.status(f'{plugin} plugin enabled')

@VisiData.api
def removePlugin(vd, plugin:str):
    path = vd.pluginConfig
    pathbackup = path.with_suffix(path.suffix + '.bak')
    try:
        shutil.copyfile(path, pathbackup)

        # Copy lines from the backup init file into its replacement, skipping lines that import the removed plugin.
        #
        # By matching from the start of a line through a word boundary, we avoid removing commented lines or inadvertently removing
        # plugins with similar names.

        r = re.compile(f'^import {plugin}\\W')
        nonimports = [line for line in vd.pluginConfigLines if not r.match(line)]
        if len(nonimports) == len(vd.pluginConfigLines):
            vd.fail("plugin not in import list")

        with path.open(mode='w', encoding='utf-8') as new:
            new.writelines(nonimports)

        sys.modules.pop(plugin)
        importlib.invalidate_caches()
        vd.warning(f'"{plugin}" plugin removed')
    except FileNotFoundError:
        vd.debug("no {vd.pluginConfig} found")


@VisiData.lazy_property
def pluginsSheet(p):
    return PluginsSheet('plugins')


class PluginsSheet(Sheet):
    rowtype = "plugins"  # rowdef: AttrDict of json dict
    colorizers = [
            CellColorizer(3, 'color_working', lambda s,c,r,v: r and r.installed)
    ]
    columns = [
        ItemColumn('name'),
        ItemColumn('installed', width=8),
        ItemColumn('description', width=60),
    ]
    nKeys = 1
    def iterload(self):
        import pkgutil
        import ast
        # enumerate installed plugins
        for name, mod in sys.modules.items():
            if name.startswith(('visidata.plugins.', 'visidata.experimental.')):
                yield AttrDict(name=name, # '.'.join(name.split('.')[2:]),
                               description=getattr(mod, '__description__', mod.__doc__),
                               installed=getattr(mod, '__version__', 'yes'),
                               maintainer=getattr(mod, '__author__', None))


BaseSheet.addCommand(None, 'open-plugins', 'vd.push(vd.pluginsSheet)', 'Open Plugins Sheet to manage supported plugins')

PluginsSheet.addCommand('a', 'add-plugin', 'enablePlugin(cursorRow.name); reload_rows()', 'Enable current plugin by adding to imports')
PluginsSheet.addCommand('d', 'delete-plugin', 'removePlugin(cursorRow.name); reload_rows()', 'Disable current plugin by removing from imports')

vd.addMenuItems('''
    System > Plugins Sheet > open-plugins
''')
