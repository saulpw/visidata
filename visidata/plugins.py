import os
import re
import zipfile

from visidata import *


option('plugins_url', 'https://visidata.org/plugins/plugins.tsv', 'source of plugins sheet')


@VisiData.lazy_property
def pluginsSheet(p):
    'Support the "plugins" phony filetype as PluginsSheet'
    return PluginsSheet('plugins', source=urlcache(options.plugins_url, days=0))

def _plugin_path(plugin):
    return Path(os.path.join(options.visidata_dir, "plugins", plugin.name+".py"))

def _plugin_init():
    return Path(os.path.join(options.visidata_dir, "plugins", "__init__.py"))

def _plugin_import(plugin):
    return "import " + _plugin_import_name(plugin)

def _plugin_import_name(plugin):
    return "plugins."+plugin.name

def _installedStatus(plugin):
    import importlib
    return '*' if importlib.util.find_spec(_plugin_import_name(plugin)) else ''

def _loadedVersion(plugin):
    name = _plugin_import_name(plugin)
    if name not in sys.modules:
        return ''
    mod = sys.modules[name]
    return getattr(mod, '__version__', 'unknown version installed')


class PluginsSheet(VisiDataMetaSheet):
    rowtype = "plugins"

    @asyncthread
    def reload(self):
        super().reload_sync()

        self.addColumn(Column('installed', getter=lambda c,r: _installedStatus(r)), index=1)
        self.addColumn(Column('loaded', getter=lambda c,r: _loadedVersion(r)), index=2)
        self.setKeys([self.column("name")])

    def installPlugin(self, plugin):
        # pip3 install requirements
        initpath = _plugin_init()
        os.makedirs(initpath.parent, exist_ok=True)
        if not initpath.exists():
            initpath.touch()

        outpath = _plugin_path(plugin)
        if outpath.exists():
            confirm("plugin path already exists, overwrite? ")

        self._install(plugin)

    @asyncthread
    def _install(self, plugin):
        exists = False
        with Path(_plugin_init()).open_text(mode='r') as fprc:
            r = re.compile(r'^{}\W'.format(_plugin_import(plugin)))
            for line in fprc.readlines():
                if r.match(line):
                    exists = True
                    warning("plugin already loaded")

        if not exists:
            outpath = _plugin_path(plugin)

            with urlcache(plugin.url, 0).open_text() as pyfp:
                with outpath.open_text(mode='w') as outfp:
                    outfp.write(pyfp.read())

            if plugin.requirements:
                p = subprocess.Popen([sys.executable, '-m', 'pip', 'install']+plugin.requirements.split())
                status(tuple(p.communicate()))

            with Path(_plugin_init()).open_text(mode='a') as fprc:
                print(_plugin_import(plugin), file=fprc)
                warning("restart visidata to use new plugin")


    def removePluginIfExists(self, plugin):
        self.removePlugin(plugin)

    def removePlugin(self, plugin):
        initpath = Path(_plugin_init())
        oldinitpath = Path(initpath.with_suffix(initpath.suffix + '.bak'))
        try:
            shutil.copyfile(initpath, oldinitpath)

            # Copy lines from the backup init file into its replacement, skipping lines that import the removed plugin.
            #
            # By matching from the start of a line through a word boundary, we avoid removing commented lines or inadvertently removing
            # plugins with similar names.
            with oldinitpath.open_text() as old, initpath.open_text(mode='w') as new:
                r = re.compile(r'^{}\W'.format(_plugin_import(plugin)))
                new.writelines(line for line in old.readlines() if not r.match(line))
            warning('plugin {0} will not be imported in the future'.format(plugin[0]))
        except FileNotFoundError:
            warning("no plugins/__init__.py found")

globalCommand(None, 'open-plugins', 'vd.push(vd.pluginsSheet)')

PluginsSheet.addCommand('a', 'add-plugin', 'installPlugin(cursorRow)')
PluginsSheet.addCommand('d', 'delete-plugin', 'removePluginIfExists(cursorRow)')
