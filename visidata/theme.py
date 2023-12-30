'Switch between packaged themes (colors and display characters)'

from visidata import vd, VisiData, Sheet, BaseSheet


vd.option('theme', '', 'display/color theme to use')

vd.themes = {}


@VisiData.before
def run(vd, *args, **kwargs):
    t = vd.options.theme
    if t:
        vd.set_theme(t)


@Sheet.api
@VisiData.api
def set_theme(obj, theme=''):
    if theme and theme not in vd.themes:
        vd.warning(f'no "{theme}" theme available')
        return

    # unset everything first
    for k in vd.options.keys():
        if k.startswith(tuple('color_ disp_ note_'.split())):
            obj.options.unset(k)

    if not theme:
        return

    if isinstance(theme, str):
        theme = vd.themes[theme]

    for k, v in theme.items():
        obj.options[k] = v


BaseSheet.addCommand('', 'theme-input', 'vd.set_theme(chooseOne([dict(key=k) for k in themes.keys()], type="theme"))', 'choose from available themes')
BaseSheet.addCommand('', 'theme-default', 'vd.set_theme()', 'reset theme to VisiData defaults')

vd.addMenuItem('View', 'Set theme', 'choose', 'theme-input')
vd.addMenuItem('View', 'Set theme', 'default', 'theme-default')
