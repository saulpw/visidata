import os
import zipfile

from visidata import *

#option('plugins_url', 'https://visidata.org/plugins/', 'source of plugins sheet')
option('plugins_url', 'file:///home/saul/git/visidata/plugins/', 'plugins url ')

globalCommand(None, 'open-plugins', 'openPlugins()')

def openPlugins():
    vs = openSource(urlcache(options.plugins_url+"plugins.tsv", 0))
    vs.name = 'visidata.org/plugins'
    vs.rowtype = "plugins"
    vs.addCommand('a', 'add-plugin', 'installPlugin(cursorRow)')
    vs.addCommand('d', 'delete-plugin', 'confirm("remove plugin? ") and removePlugin(cursorRow)')
    vd.push(vs)

def plugin_url(pluginname):
    return options.plugins_url+pluginname+".zip"

def plugin_path(pluginname):
    return Path(os.path.join(options.visidata_dir, "plugins", pluginname))

def plugin_import(pluginname):
    return "import plugins."+pluginname

@VisiData.api
def installPlugin(vd, plugin):
    # pip3 install requirements
    outpath = plugin_path(plugin.name)
    if outpath.exists():
        confirm("plugin path already exists, overwrite? ")

    _install(plugin)


@asyncthread
def _install(plugin):
    outpath = plugin_path(plugin.name)
    with zipfile.ZipFile(urlcache(plugin_url(plugin.name), text=False).open_bytes()) as zf:
        zf.extractall(path=outpath.resolve())

    p = subprocess.Popen(['pip3', 'install']+plugin.requirements.split())
    status(tuple(p.communicate()))

    with Path(options.config).open_text(mode='a') as fprc:
        print(plugin_import(plugin.name), file=fprc)

    warning("restart visidata to use new plugin")


def removePlugin(plugin):
    vdrc = Path(options.config).resolve()
    oldvdrc = vdrc+'.bak'
    try:
        shutil.copyfile(vdrc, oldvdrc)
        vdrc_contents = Path(oldvdrc).read_text().replace(plugin_import(plugin.name), '')

        with Path(options.config).open_text(mode='w') as fprc:  # replace without import line
            fprc.write(vdrc_contents)
    except FileNotFoundError:
        warning("no visidatarc file")

    try:
        shutil.rmtree(plugin_path(plugin.name).resolve())
    except FileNotFoundError:
        warning("%s plugin not installed" % plugin.name)
