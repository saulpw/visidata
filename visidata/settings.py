import collections
import sys
import inspect
import argparse
import importlib
import os

import visidata
from visidata import VisiData, BaseSheet, vd, AttrDict
from visidata.vendor.appdirs import user_config_dir, user_cache_dir


# [settingname] -> { objname(Sheet-instance/Sheet-type/'global'/'default'): Option/Command/longname }
class SettingsMgr(collections.OrderedDict):
    def __init__(self):
        super().__init__()
        self.allobjs = {}

    def objname(self, obj):
        if isinstance(obj, str):
            v = obj
        elif obj is None:
            v = 'global'
        elif isinstance(obj, BaseSheet):
            v = obj.name
        elif inspect.isclass(obj) and issubclass(obj, BaseSheet):
            v = obj.__name__
        else:
            return None

        self.allobjs[v] = obj
        return v

    def getobj(self, objname):
        'Inverse of objname(obj); returns obj if available'
        return self.allobjs.get(objname)

    def unset(self, k, obj='default'):
        'Remove setting for given key in the given context.'
        objstr = self.objname(obj)
        if objstr in self[k]:
            del self[k][objstr]

    def set(self, k, v, obj):
        'obj is a Sheet instance, or a Sheet [sub]class.  obj="global" means override default unless there is a sheet-specific override; obj="default" means last resort.'
        if k not in self:
            self[k] = dict()
        self[k][self.objname(obj)] = v
        return v

    def setdefault(self, k, v):
        return self.set(k, v, 'default')

    def _mappings(self, obj):
        '''Return list of contexts in order to resolve settings. ordering is, from lowest to highest precedence:

        1. "default": default specified in option() definition
        2. "global": in order of program execution:
            a. .visidatarc
            b. command-line options, applied on top of the overrides in .visidatarc
            c. at runtime via 'O'ptions meta-sheet
        3. objname(type(obj)): current sheet class and parents, recursively
        4. objname(obj): the specific sheet instance
            a. can override at runtime, replace value for sheet instance
        '''
        mappings = []
        if obj:
            mappings += [self.objname(obj)]
            mappings += [self.objname(cls) for cls in inspect.getmro(type(obj))]

        mappings += ['global', 'default']
        return mappings

    def _get(self, key, obj=None):
        d = self.get(key, None)
        if d:
            for m in self._mappings(obj or vd.activeSheet):
                v = d.get(m)
                if v:
                    return v

    def iter(self, obj=None):
        'Iterate through all keys considering context of obj. If obj is None, uses the context of the top sheet.'
        if obj is None and vd:
            obj = vd.activeSheet

        for o in self._mappings(obj):
            for k in self.keys():
                for o2 in self[k]:
                    if o == o2:
                        yield (k, o), self[k][o2]

    def iterall(self):
        for k in self.keys():
            for o in self[k]:
                yield (k, o), self[k][o]



class Command:
    def __init__(self, longname, execstr, helpstr=''):
        self.longname = longname
        self.execstr = execstr
        self.helpstr = helpstr


class Option:
    def __init__(self, name, value, helpstr=''):
        self.name = name
        self.value = value
        self.helpstr = helpstr
        self.replayable = False
        self.sheettype = BaseSheet

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.name == other.name


@VisiData.api
class OptionsObject:
    'minimalist options framework'
    def __init__(self, mgr, obj=None):
        object.__setattr__(self, '_opts', mgr)
        object.__setattr__(self, '_cache', {})
        object.__setattr__(self, '_obj', obj)

    def keys(self, obj=None):
        for k, d in self._opts.items():
            if obj is None or self._opts.objname(obj) in d:
                yield k

    def _get(self, k, obj=None):
        'Return Option object for k in context of obj. Cache result until any set().'
        opt = self._cache.get((k, obj or vd.activeSheet), None)
        if opt is None:
            opt = self._opts._get(k, obj)
            self._cache[(k, obj or vd.activeSheet)] = opt
        return opt

    def _set(self, k, v, obj=None, helpstr=''):
        self._cache.clear()  # invalidate entire cache on any change
        return self._opts.set(k, Option(k, v, helpstr), obj)

    def is_set(self, k, obj=None):
        d = self._opts.get(k, None)
        if d:
            return d.get(self._opts.objname(obj), None)

    def get(self, optname, default=None):
        'Return the value of the given *optname* option in the options context. *default* is only returned if the option is not defined.  An Exception is never raised.'
        d = self._get(optname, None)
        if d:
            return d.value
        return default

    def getobj(self, optname, obj=None):
        'Return value of option optname as set on obj, or on option context if obj is None.'
        return self._get(optname, obj).value

    def getdefault(self, optname):
        return self._get(optname, 'default').value

    def getonly(self, optname, obj, default):
        'Return value of option optname as set on obj, or default if not set specifically on obj'
        d = self._opts.get(optname, None)
        if d:
            opt = d.get(self._opts.objname(obj), None)
            if opt:
                return opt.value
        return default

    def set(self, optname, value, obj='global'):
        "Override *value* for *optname* in the options context, or in the *obj* context if given."
        opt = self._get(optname)
        if opt:
            curval = opt.value
            t = type(curval)
            if value is None and curval is not None:
                return self.unset(optname, obj=obj)
            elif isinstance(value, str) and t is bool: # special case for bool options
                value = value and (value[0] not in "0fFnN")  # ''/0/false/no are false, everything else is true
            elif type(value) is t:    # if right type, no conversion
                pass
            elif curval is None:  # if None, do not apply type conversion
                pass
            else:
                value = t(value)

            if curval != value and self._get(optname, 'default').replayable:
                if obj != 'default' and type(obj) is not type:  # default and class options set on init aren't recorded
                    if vd.cmdlog:
                        objname = self._opts.objname(obj)
                        vd.cmdlog.addRow(vd.cmdlog.newRow(sheet=objname, row=optname,
                                    keystrokes='', input=str(value),
                                    longname='set-option', undofuncs=[]))
        else:
            curval = None
            vd.warning('setting unknown option %s' % optname)

        return self._set(optname, value, obj)

    def unset(self, optname, obj=None):
        'Remove setting value for given context.'
        v = self._opts.unset(optname, obj)
        opt = self._get(optname)
        if vd.cmdlog and opt and opt.replayable:
            objname = self._opts.objname(obj)
            vd.cmdlog.addRow(vd.cmdlog.newRow(sheet=objname, row=optname,
                            keystrokes='', input='',
                            longname='unset-option'))
        self._cache.clear()  # invalidate entire cache on any change
        return v

    def setdefault(self, optname, value, helpstr):
        return self._set(optname, value, 'default', helpstr=helpstr)

    def getall(self, prefix=''):
        'Return dictionary of all options beginning with `prefix` (with `prefix` removed from the name).'
        return { optname[len(prefix):] : vd.options[optname]
                    for optname in vd.options.keys()
                        if optname.startswith(prefix) }

    def __getattr__(self, optname):      # options.foo
        'Return value of option `optname` for stored options context.'
        return self.__getitem__(optname)

    def __setattr__(self, optname, value):   # options.foo = value
        'Set *value* of option *optname* for stored options context.'
        self.__setitem__(optname, value)

    def __getitem__(self, optname):      # options[optname]
        opt = self._get(optname, obj=self._obj)
        if not opt:
            raise ValueError('no option "%s"' % optname)
        return opt.value

    def __setitem__(self, optname, value):   # options[optname] = value
        self.set(optname, value, obj=self._obj)


vd.commands = SettingsMgr()
vd.bindkeys = SettingsMgr()
vd._options = SettingsMgr()

vd.options = vd.OptionsObject(vd._options)  # global option settings


@VisiData.api
def option(vd, name, default, helpstr, replay=False, sheettype=BaseSheet):
    '''Declare a new option.

   - `name`: name of option
   - `default`: default value when no other override exists
   - `helpstr`: short description of option (as shown in the **Options Sheet**)
   - `replay`: ``True`` if changes to the option should be stored in the **Command Log**
   - `sheettype`: ``None`` if the option is not sheet-specific, to make it global on CLI
    '''
    opt = vd.options.setdefault(name, default, helpstr)
    opt.replayable = replay
    opt.sheettype=sheettype
    return opt


@BaseSheet.class_api
@classmethod
def addCommand(cls, keystrokes, longname, execstr, helpstr='', **kwargs):
    '''Add a new command to *cls* sheet type.

    - *keystrokes*: default keybinding, including **prefixes**.
    - *longname*: name of the command.
    - *execstr*: Python statement to pass to `exec()`'ed when the command is executed.
    - *helpstr*: help string shown in the **Commands Sheet**.
    '''
    vd.commands.set(longname, Command(longname, execstr, helpstr=helpstr, **kwargs), cls)
    if keystrokes:
        vd.bindkeys.set(vd.prettykeys(keystrokes), longname, cls)
    return longname

def _command(cls, binding, longname, helpstr, **kwargs):
    def decorator(func):
        funcname = longname.replace('-', '_')
        setattr(vd, funcname, func)
        cls.addCommand(binding, longname, f'vd.{funcname}(sheet)', helpstr, **kwargs)
    return decorator

BaseSheet.command = classmethod(_command)
globalCommand = BaseSheet.addCommand

@VisiData.api
def bindkey(vd, keystrokes, longname):
    'Bind *keystrokes* to *longname* on BaseSheet and unbind more-specific bindings of keystrokes.'
    vd.bindkeys[vd.prettykeys(keystrokes)] = {'BaseSheet': longname}

@BaseSheet.class_api
@classmethod
def bindkey(cls, keystrokes, longname):
    'Bind *keystrokes* to *longname* on the *cls* sheet type.'
    oldlongname = vd.bindkeys._get(keystrokes, cls)
    if oldlongname:
        vd.warning('%s was already bound to %s' % (keystrokes, oldlongname))
    vd.bindkeys.set(vd.prettykeys(keystrokes), longname, cls)

@BaseSheet.class_api
@classmethod
def unbindkey(cls, keystrokes):
    '''Unbind `keystrokes` on a `<SheetType>`.
    May be necessary to avoid a warning when overriding a binding on the same exact class.'''
    vd.bindkeys.unset(vd.prettykeys(keystrokes), cls)

@BaseSheet.api
def getCommand(sheet, cmd):
    'Return the Command for the given *cmd*, which may be keystrokes, longname, or a Command itself, within the context of `sheet`.'
    if isinstance(cmd, Command):
        return cmd

    longname = cmd
    while vd.bindkeys._get(longname, obj=sheet):
        longname = vd.bindkeys._get(longname, obj=sheet)

    return vd.commands._get(longname, obj=sheet)


@VisiData.api
def loadConfigFile(vd, fn='', _globals=None):
    p = visidata.Path(fn or vd.options.config)
    if _globals is None:
        _globals = vd.getGlobals()
    if p.exists():
        try:
            with open(p) as fd:
                code = compile(fd.read(), str(p), 'exec')
            exec(code, _globals)
        except Exception as e:
            vd.exceptionCaught(e)

    vd.addGlobals(_globals)


def addOptions(parser):
    for optname in vd.options.keys('default'):
        if optname.startswith('color_') or optname.startswith('disp_'):
            continue
        action = 'store_true' if options[optname] is False else 'store'
        try:
            parser.add_argument('--' + optname.replace('_', '-'), action=action, dest=optname, default=None, help=options._opts._get(optname).helpstr)
        except argparse.ArgumentError:
            pass


def _get_config_file():
    xdg_config_file = visidata.Path(user_config_dir('visidata')) / 'config.py'
    if xdg_config_file.exists():
        return xdg_config_file
    else:
        return visidata.Path('~/.visidatarc')


def _get_cache_dir():
    return visidata.Path(user_cache_dir('visidata'))


@VisiData.api
def loadConfigAndPlugins(vd, args=AttrDict()):
    # set visidata_dir and config manually before loading config file, so visidata_dir can be set from cli or from $VD_DIR
    vd.options.visidata_dir = args.visidata_dir if args.visidata_dir is not None else os.getenv('VD_DIR', '') or vd.options.visidata_dir
    vd.options.config = args.config if args.config is not None else os.getenv('VD_CONFIG', '') or vd.options.config

    sys.path.append(str(visidata.Path(vd.options.visidata_dir)))
    sys.path.append(str(visidata.Path(vd.options.visidata_dir)/"plugins-deps"))

    # import plugins from .visidata/plugins before .visidatarc, so plugin options can be overridden
    for modname in (args.imports or vd.options.imports or '').split():
        try:
            vd.addGlobals(importlib.import_module(modname).__dict__)
        except ModuleNotFoundError as e:
            # issue #1131
            if 'plugins' in e.args[0]:
                continue
            vd.exceptionCaught(e)
        except Exception as e:
            vd.exceptionCaught(e)
            continue

    # user customisations in config file in standard location
    vd.loadConfigFile(vd.options.config, vd.getGlobals())


vd.option('visidata_dir', '~/.visidata/', 'directory to load and store additional files', sheettype=None)

BaseSheet.bindkey('^M', '^J')  # for windows ENTER
BaseSheet.addCommand('gO', 'open-config', 'vd.push(open_txt(Path(options.config)))', 'open options.config as text sheet')

vd.addGlobals({
    'options': vd.options,  # legacy
    'globalCommand': BaseSheet.addCommand,
    'Option': Option,
})
