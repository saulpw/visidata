import os
import re
import zipfile
import importlib

from visidata import *


vd.option('plugins_url', 'https://visidata.org/plugins/plugins.jsonl', 'source of plugins sheet')


@VisiData.lazy_property
def pluginsSheet(p):
    return PluginsSheet('plugins_global')

def _plugin_path(plugin):
    return Path(os.path.join(options.visidata_dir, "plugins", plugin.name+".py"))

def _plugin_init():
    return Path(os.path.join(options.visidata_dir, "plugins", "__init__.py"))

def _plugin_import(plugin):
    return "import " + _plugin_import_name(plugin)

def _plugin_import_name(plugin):
    if 'git+' in plugin.url:
        return plugin.name
    return "plugins."+plugin.name

def _plugin_in_import_list(plugin):
    with Path(_plugin_init()).open_text(mode='r', encoding='utf-8') as fprc:
        r = re.compile(r'^{}\W'.format(_plugin_import(plugin)))
        for line in fprc.readlines():
            if r.match(line):
                return True

def _installedStatus(col, plugin):
    return '*' if importlib.util.find_spec(_plugin_import_name(plugin)) else ''

def _loadedVersion(plugin):
    name = _plugin_import_name(plugin)
    if name not in sys.modules:
        return ''
    mod = sys.modules[name]
    return getattr(mod, '__version__', 'unknown version installed')

def _checkHash(data, sha):
    import hashlib
    return hashlib.sha256(data.strip().encode('utf-8')).hexdigest() == sha

def _pluginColorizer(s,c,r,v):
    if not r: return None
    ver = _loadedVersion(r)
    if not ver: return None
    if ver != r.latest_ver: return 'color_warning'
    return 'color_working'


@VisiData.api
def pipinstall(vd, deps):
    'Install *deps*, a list of pypi modules to install via pip into the plugins-deps directory. Return True if successful (no error).'
    p = subprocess.Popen([sys.executable, '-m', 'pip', 'install',
                        '--target', str(Path(options.visidata_dir)/"plugins-deps"),
                      ] + deps,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    out, err = p.communicate()
    vd.status(out.decode())
    if err:
        vd.warning(err.decode())
        return False
    return True


class PluginsSheet(JsonLinesSheet):
    rowtype = "plugins"  # rowdef: AttrDict of json dict
    colorizers = [
        CellColorizer(3, None, _pluginColorizer)
    ]

    def iterload(self):
        for r in JsonLinesSheet.iterload(self):
            yield AttrDict(r)

    @asyncsingle
    def reload(self):
        self.source = urlcache(options.plugins_url or vd.fail(), days=1)  # for VisiDataMetaSheet.reload()
        super().reload.__wrapped__(self)
        self.addColumn(Column('available', width=0, getter=_installedStatus), index=1)
        self.addColumn(Column('installed', width=8, getter=lambda c,r: _loadedVersion(r)), index=2)
        self.column('description').width = 40
        self.setKeys([self.column("name")])

        for r in Progress(self.rows):
            for funcname in (r.provides or '').split():
                func = lambda *args, **kwargs: vd.fail('this requires the %s plugin' % r.name)
                vd.addGlobals({funcname: func})
                setattr(vd, funcname, func)


    def installPlugin(self, plugin):
        # pip3 install requirements
        initpath = _plugin_init()
        os.makedirs(initpath.parent, exist_ok=True)
        if not initpath.exists():
            initpath.touch()

        outpath = _plugin_path(plugin)
        overwrite = True
        if outpath.exists():
            try:
                vd.confirm("plugin path already exists, overwrite? ")
            except ExpectedException:
                overwrite = False
                if _plugin_in_import_list(plugin):
                    vd.fail("plugin already loaded")
                else:
                    self._loadPlugin(plugin)
        if overwrite:
            self._install(plugin)

    @asyncthread
    def _install(self, plugin):
        outpath = _plugin_path(plugin)

        if "git+" in plugin.url:
            p = subprocess.Popen([sys.executable, '-m', 'pip', 'install',
                                '--upgrade', plugin.url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            out, err = p.communicate()
            vd.status(out.decode())
            if err:
                vd.warning(err.decode())
        else:
            with urlcache(plugin.url, days=0).open_text(encoding='utf-8') as pyfp:
                contents = pyfp.read()
                if not _checkHash(contents, plugin.sha256):
                    vd.error('%s plugin SHA256 does not match!' % plugin.name)
                with outpath.open_text(mode='w', encoding='utf-8') as outfp:
                    outfp.write(contents)

        if plugin.pydeps:
            vd.pipinstall(plugin.pydeps.split())

        vd.status('%s plugin installed' % plugin.name)

        if _plugin_in_import_list(plugin):
            vd.warning("plugin already loaded")
        else:
            self._loadPlugin(plugin)


    def _loadPlugin(self, plugin):
        with Path(_plugin_init()).open_text(mode='a', encoding='utf-8') as fprc:
            print(_plugin_import(plugin), file=fprc)
            importlib.import_module(_plugin_import_name(plugin))
            vd.status('%s plugin loaded' % plugin.name)


    def removePluginIfExists(self, plugin):
        self.removePlugin(plugin)

    def removePlugin(self, plugin):
        if not _plugin_in_import_list(plugin):
            vd.fail("plugin not in import list")

        initpath = Path(_plugin_init())
        oldinitpath = Path(initpath.with_suffix(initpath.suffix + '.bak'))
        try:
            shutil.copyfile(initpath, oldinitpath)

            # Copy lines from the backup init file into its replacement, skipping lines that import the removed plugin.
            #
            # By matching from the start of a line through a word boundary, we avoid removing commented lines or inadvertently removing
            # plugins with similar names.
            with oldinitpath.open_text(encoding='utf-8') as old, initpath.open_text(mode='w', encoding='utf-8') as new:
                r = re.compile(r'^{}\W'.format(_plugin_import(plugin)))
                new.writelines(line for line in old.readlines() if not r.match(line))

            if os.path.exists(_plugin_path(plugin)):
                os.unlink(_plugin_path(plugin))
            sys.modules.pop(_plugin_import_name(plugin))
            importlib.invalidate_caches()
            vd.warning('{0} plugin uninstalled'.format(plugin['name']))
        except FileNotFoundError:
            vd.warning("no plugins/__init__.py found")


BaseSheet.addCommand(None, 'open-plugins', 'vd.push(vd.pluginsSheet)', 'Open Plugins Sheet to manage supported plugins')

PluginsSheet.addCommand('a', 'add-plugin', 'installPlugin(cursorRow)', 'Install and enable current plugin')
PluginsSheet.addCommand('d', 'delete-plugin', 'removePluginIfExists(cursorRow)', 'Disable current plugin')
