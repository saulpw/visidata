import os
import zipfile

from visidata import *


option('plugins_url', 'https://visidata.org/plugins/plugins.tsv', 'source of plugins sheet')


@VisiData.cached_property
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


class PluginsSheet(TsvSheet):
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
        if not initpath.exists():
            with initpath.open_text(mode='w') as initfp:
                initfp.write()

        outpath = _plugin_path(plugin)
        if outpath.exists():
            confirm("plugin path already exists, overwrite? ")

        self._install(plugin)

    @asyncthread
    def _install(self, plugin):
        outpath = _plugin_path(plugin)
        os.makedirs(outpath.parent, exist_ok=True)

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
        oldinitpath = initpath.with_suffix(initpath.suffix + '.bak')
        try:
            shutil.copyfile(initpath, oldinitpath)
            init_contents = Path(oldinitpath).read_text().replace('\n'+_plugin_import(plugin), '')

            with Path(_plugin_init()).open_text(mode='w') as fprc:  # replace without import line
                fprc.write(init_contents)
            warning('plugin {0} will not be imported in the future'.format(plugin[0]))
        except FileNotFoundError:
            warning("no plugins/__init__.py found")

globalCommand(None, 'open-plugins', 'vd.push(vd.pluginsSheet)')

PluginsSheet.addCommand('a', 'add-plugin', 'installPlugin(cursorRow)')
PluginsSheet.addCommand('d', 'delete-plugin', 'removePluginIfExists(cursorRow)')
