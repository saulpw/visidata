import collections
import sys
import inspect
import argparse

import visidata
from visidata import VisiData, BaseSheet, vd, getGlobals, addGlobals


# [settingname] -> { objname(Sheet-instance/Sheet-type/'override'/'global'): Option/Command/longname }
class SettingsMgr(collections.OrderedDict):
    def __init__(self):
        super().__init__()
        self.allobjs = {}

    def objname(self, obj):
        if isinstance(obj, str):
            v = obj
        elif obj is None:
            v = 'override'
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

    def unset(self, k, obj='global'):
        'Remove setting for given key in the given context.'
        objstr = self.objname(obj)
        if objstr in self[k]:
            del self[k][objstr]

    def set(self, k, v, obj):
        'obj is a Sheet instance, or a Sheet [sub]class.  obj="override" means override all; obj="global" means last resort.'
        if k not in self:
            self[k] = dict()
        self[k][self.objname(obj)] = v
        return v

    def setdefault(self, k, v):
        return self.set(k, v, 'global')

    def _mappings(self, obj):
        '''Return list of contexts in order to resolve settings. ordering is, from lowest to highest precedence:

        1. "global": default specified in option() definition
        2. "override": in order of program execution:
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

        mappings += ['override', 'global']
        return mappings

    def _get(self, key, obj=None):
        d = self.get(key, None)
        if d:
            for m in self._mappings(obj or vd.sheet):
                v = d.get(m)
                if v:
                    return v

    def iter(self, obj=None):
        'Iterate through all keys considering context of obj. If obj is None, uses the context of the top sheet.'
        if obj is None and vd:
            obj = vd.sheet

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

def globalCommand(keystrokes, longname, execstr, helpstr='', **kwargs):
    commands.setdefault(longname, Command(longname, execstr, helpstr=helpstr, **kwargs))

    if keystrokes:
        assert not bindkeys._get(keystrokes), keystrokes
        bindkeys.setdefault(keystrokes, longname)


class Option:
    def __init__(self, name, value, helpstr=''):
        self.name = name
        self.value = value
        self.helpstr = helpstr
        self.replayable = False

    def __str__(self):
        return str(self.value)


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
        opt = self._cache.get((k, obj), None)
        if opt is None:
            opt = self._opts._get(k, obj)
            self._cache[(k, obj or vd.sheet)] = opt
        return opt

    def _set(self, k, v, obj=None, helpstr=''):
        self._cache.clear()  # invalidate entire cache on any set()
        return self._opts.set(k, Option(k, v, helpstr), obj)

    def get(self, k, obj=None):
        return self._get(k, obj).value

    def getdefault(self, k):
        return self._get(k, 'global').value

    def set(self, k, v, obj='override'):
        opt = self._get(k)
        if opt:
            curval = opt.value
            t = type(curval)
            if v is None and curval is not None:
                v = t()           # empty value
            elif isinstance(v, str) and t is bool: # special case for bool options
                v = v and (v[0] not in "0fFnN")  # ''/0/false/no are false, everything else is true
            elif type(v) is t:    # if right type, no conversion
                pass
            elif curval is None:  # if None, do not apply type conversion
                pass
            else:
                v = t(v)

            if curval != v and self._get(k, 'global').replayable:
                if vd.cmdlog:  # options set on init aren't recorded
                    vd.set_option(vd.cmdlog, k, v, obj)
        else:
            curval = None
            vd.warning('setting unknown option %s' % k)

        return self._set(k, v, obj)

    def unset(self, k, obj='override'):
        'Remove setting value for given context.'
        self._opts.unset(k, obj)

    def setdefault(self, k, v, helpstr):
        return self._set(k, v, 'global', helpstr=helpstr)

    def getall(self, kmatch):
        return {obj:opt for (k, obj), opt in self._opts.items() if k == kmatch}

    def __getattr__(self, k):      # options.foo
        return self.__getitem__(k)

    def __setattr__(self, k, v):   # options.foo = v
        self.__setitem__(k, v)

    def __getitem__(self, k):      # options[k]
        opt = self._get(k, obj=self._obj)
        if not opt:
            vd.error('no option "%s"' % k)
        return opt.value

    def __setitem__(self, k, v):   # options[k] = v
        self.set(k, v, obj=self._obj)

    def __call__(self, prefix=''):
        return { optname[len(prefix):] : options[optname]
                    for optname in options.keys()
                        if optname.startswith(prefix) }


commands = SettingsMgr()
bindkeys = SettingsMgr()
vd._options = SettingsMgr()
options = vd.OptionsObject(vd._options)


def option(name, default, helpstr, replay=False):
    opt = options.setdefault(name, default, helpstr)
    opt.replayable = replay
    return opt

theme = option

@VisiData.api
def addCommand(vd, keystrokes, longname, execstr, helpstr='', **kwargs):
    globalCommand(keystrokes, longname, execstr, helpstr=helpstr, **kwargs)

@BaseSheet.class_api
@classmethod
def addCommand(cls, keystrokes, longname, execstr, helpstr='', **kwargs):
    commands.set(longname, Command(longname, execstr, helpstr=helpstr, **kwargs), cls)
    if keystrokes:
        bindkeys.set(keystrokes, longname, cls)

@BaseSheet.class_api
@classmethod
def bindkey(cls, keystrokes, longname):
    oldlongname = bindkeys._get(keystrokes, cls)
    if oldlongname:
        vd.warning('%s was already bound to %s' % (keystrokes, oldlongname))
    bindkeys.set(keystrokes, longname, cls)

@BaseSheet.class_api
@classmethod
def unbindkey(cls, keystrokes):
    bindkeys.unset(keystrokes, cls)

@BaseSheet.api
def getCommand(self, keystrokes_or_longname):
    longname = bindkeys._get(keystrokes_or_longname)
    try:
        if longname:
            return commands._get(longname) or vd.fail('no command "%s"' % longname)
        else:
            return commands._get(keystrokes_or_longname) or vd.fail('no binding for %s' % keystrokes_or_longname)
    except Exception as exc:
        return None


def loadConfigFile(fnrc, _globals=None):
    p = visidata.Path(fnrc)
    if _globals is None:
        _globals = globals()
    if p.exists():
        try:
            code = compile(open(p).read(), str(p), 'exec')
            exec(code, _globals)
        except Exception as e:
            vd.exceptionCaught(e)

    addGlobals(_globals)


def addOptions(parser):
    for optname in options.keys('global'):
        if optname.startswith('color_') or optname.startswith('disp_'):
            continue
        action = 'store_true' if options[optname] is False else 'store'
        try:
            parser.add_argument('--' + optname.replace('_', '-'), action=action, dest=optname, default=None, help=options._opts._get(optname).helpstr)
        except argparse.ArgumentError:
            pass


@VisiData.api
def parseArgs(vd, parser:argparse.ArgumentParser):
    addOptions(parser)
    args, remaining = parser.parse_known_args()

    # add visidata_dir to path before loading config file (can only be set from cli)
    sys.path.append(str(visidata.Path(args.visidata_dir or options.visidata_dir)))

    # user customisations in config file in standard location
    loadConfigFile(visidata.Path(args.config or options.config), getGlobals())

    # add plugin options and reparse
    addOptions(parser)
    args, remaining = parser.parse_known_args()

    # apply command-line overrides after .visidatarc
    for optname, optval in vars(args).items():
        if optval is not None and optname not in ['inputs', 'play', 'batch', 'output', 'diff']:
            options[optname] = optval

    return args


def bindkey(keystrokes, longname):
    bindkeys.setdefault(keystrokes, longname)

def bindkey_override(keystrokes, longname):
    bindkeys.set(keystrokes, longname)

def unbindkey(keystrokes):
    bindkeys.unset(keystrokes)


BaseSheet.addCommand(None, 'open-config', 'fn=options.config; vd.push(TextSheet(fn, source=Path(fn)))', 'open ~/.visidatarc as Text Sheet')
