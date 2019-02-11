import os
import zipfile

from visidata import *


option('plugins_url', 'https://visidata.org/plugins/', 'source of plugins sheet')

@VisiData.api
def openPlugins(vd):
    return openSource(urlcache(options.plugins_url+"plugins.tsv", 0), filetype="plugins")

def open_plugins(p):
    'Support the "plugins" phony filetype as PluginsSheet'
    return PluginsSheet('visidata.org/plugins', source=p)

def _plugin_zip(plugin):
    return "%s%s-%s.zip" % (options.plugins_url, plugin.name, plugin.plugin_ver)

def _plugin_path(plugin):
    return Path(os.path.join(options.visidata_dir, "plugins", plugin.name))

def _plugin_import(plugin):
    return "import " + _plugin_import_name(plugin)

def _plugin_import_name(plugin):
    return "plugins."+plugin.name


class PluginsSheet(TsvSheet):
    rowtype = "plugins"

    @asyncthread
    def reload(self):
        vd.sync(super().reload())

        self.addColumn(Column('installed', getter=lambda c,r: c.sheet.installedStatus(r)), index=1)
        self.addColumn(Column('loaded', getter=lambda c,r: c.sheet.loadedVersion(r)), index=2)

    def installedStatus(self, plugin):
        import importlib
        return importlib.util.find_spec(_plugin_import_name(plugin))

    def loadedVersion(self, plugin):
        name = _plugin_import_name(plugin)
        if name not in sys.modules:
            return None
        mod = getattr(__import__(name), name)
        return getattr(mod, '__version__', 'unknown version installed')

    def installPlugin(self, plugin):
        # pip3 install requirements
        outpath = _plugin_path(plugin)
        if outpath.exists():
            confirm("plugin path already exists, overwrite? ")

        self._install(plugin)

    @asyncthread
    def _install(self, plugin):
        outpath = _plugin_path(plugin)
        with zipfile.ZipFile(urlcache(_plugin_zip(plugin), text=False).open_bytes()) as zf:
            zf.extractall(path=outpath.resolve())

        p = subprocess.Popen(['pip3', 'install']+plugin.requirements.split())
        status(tuple(p.communicate()))

        with Path(options.config).open_text(mode='a') as fprc:
            print(_plugin_import(plugin), file=fprc)

        warning("restart visidata to use new plugin")

    def removePluginIfExists(self, plugin):
        ver = loadedVersion()
        if not ver:
            warning('plugin is not installed')
            return

        confirm("remove plugin? ")
        self.removePlugin(plugin)

    def removePlugin(self, plugin):
        vdrc = Path(options.config).resolve()
        oldvdrc = vdrc+'.bak'
        try:
            shutil.copyfile(vdrc, oldvdrc)
            vdrc_contents = Path(oldvdrc).read_text().replace('\n'+_plugin_import(plugin), '')

            with Path(options.config).open_text(mode='w') as fprc:  # replace without import line
                fprc.write(vdrc_contents)
        except FileNotFoundError:
            warning("no visidatarc file")

        try:
            shutil.rmtree(_plugin_path(plugin).resolve())
        except FileNotFoundError:
            warning("%s plugin not installed" % plugin.name)


globalCommand(None, 'open-plugins', 'vd.push(openPlugins())')

PluginsSheet.addCommand('a', 'add-plugin', 'installPlugin(cursorRow)')
PluginsSheet.addCommand('d', 'delete-plugin', 'removePluginIfExists(cursorRow)')
