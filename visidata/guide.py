'''
# A Guide to VisiData Guides
Each guide shows you how to use a particular feature in VisiData. Gray guides have not been written yet. We love contributions: [:onclick https://visidata.org/docs/api/guides]https://visidata.org/docs/api/guides[/].

- [:keystrokes]Up/Down[/] to move the row cursor
- [:keystrokes]Enter[/] to view a topic
'''
import re

from visidata import vd, BaseSheet, Sheet, ItemColumn, Column, VisiData, ENTER, RowColorizer, AttrDict, MissingAttrFormatter
from visidata import wraptext

guides_list = '''
GuideIndex ("A Guide to VisiData Guides (you are here)")
HelpGuide ("Where to Start and How to Quit")  # manpage; ask for patreon
MenuGuide ("The VisiData Menu System")
CommandsSheet ("How to find the command you want run")

#  real barebones basics
MovementGuide ("Movement and search")
InputGuide ("Input keystrokes")
SortGuide ("Sorting")
ColumnsGuide ("Rename, hide, and resize columns")
TypesSheet ("Column types")
CommandLog  ("Undo and Replay")

#  rev this thing up

SelectionGuide ("Selecting and filtering") # stu|, and variants; filtering with dup-sheet; g prefix often refers to selected rowset
SheetsSheet  ("The Sheet Stack")
ColumnsSheet ("Columns: the only way to fly")
StatusesSheet ("Revisit old status messages")
SidebarSheet ("Dive into the sidebar")
SaversGuide ("Saving Data")  # talk about options.overwrite + ro here

ErrorsSheet ("What was that error?")
ModifyGuide ("Adding, Editing, Deleting Rows")

# the varieties of data experience

SlideGuide ("Sliding rows and columns around")
ExprGuide ("Compute Python over every row")
JoinGuide ("Joining multiple sheets together")
DescribeSheet ("Basic Statistics (min/max/mode/median/mean)")
AggregatorsSheet ("Aggregations like sum, mean, and distinct")
FrequencyTable ("Frequency Tables are how you GROUP BY")
PivotGuide ("Pivot Tables are just Frequency Tables with more columns")
MeltGuide ("Melt is just Unpivot")
JsonGuide ("Some special features for JSON") # with expand/contract, unfurl
RegexGuide ("Matching and Transforming Strings with Regex")
GraphSheet ("Basic scatterplots and other graphs")
WindowFunctionGuide ("Perform operations on groups of rows")

# for the frequent user
OptionsSheet ("Options and Settings")
ClipboardGuide ("Copy and Paste Data via the Clipboard")
DirSheet ("Browsing the local filesystem")
FormatsSheet ("What can you open with VisiData?")
SplitpaneGuide ("Split VisiData into two panes")
ThemesSheet ("Change Interface Theme")
ColorSheet ("See available colors")
MacrosSheet ("Recording macros")
MemorySheet ("Making note of certain values")

# advanced usage and developers

ThreadsSheet ("Threads past and present")
PyobjSheet ("Inspecting internal Python objects")

#  appendices

InputEditorGuide ("Using the builtin line editor")
'''

vd.guides = {}  # name -> guidecls

@VisiData.api
def addGuide(vd, name, guidecls):
    vd.guides[name] = guidecls

@VisiData.api
class GuideIndex(Sheet):
    guide = __doc__

    rowtype = 'guides' # rowdef: list(guide number, guide name, topic description, points, max_points)
    columns = [
        ItemColumn('n', 0, type=int),
        ItemColumn('name', 1, width=0),
        ItemColumn('topic', 2, width=60),
    ]
    colorizers = [
            RowColorizer(7, 'color_guide_unwritten', lambda s,c,r,v: r and r[1] not in vd.guides)
            ]
    def iterload(self):
        i = 0
        for line in guides_list.splitlines():
            m = re.search(r'(\w+?) \("(.*)"\)', line)
            if m:
                yield [i] + list(m.groups())
                i += 1

    def openRow(self, row):
        name = row[1]
        return vd.getGuide(name)

class OptionHelpGetter:
    'For easy and consistent formatting in sidebars and helpstrings, use {vd.options.help.opt_name}.'
    def __getattr__(self, optname):
        opt = vd.options._get(optname, 'default')
        return f'[:onclick options-sheet {optname}][:longname]{optname}[/][/]: to {opt.helpstr} (default: {opt.value})'


class CommandHelpGetter:
    'For easy and consistent formatting in sidebars and helpstrings, use {vd.commands.help.long_name}.'
    def __init__(self, cls):
        self.cls = cls
        self.helpsheet = vd.HelpSheet()
        self.helpsheet.ensureLoaded()

    def __getattr__(self, k):
        return self.__getitem__(k)

    def __getitem__(self, k):
        longname = k.replace('_', '-')
        binding = self.helpsheet.revbinds.get(longname, [None])[0]
        # cmddict has a SheetClass associated with each command
        # go through all the parents of the Sheet type, to look for the command
        for cls in self.cls.superclasses():
            cmd = self.helpsheet.cmddict.get((cls.__name__, longname), None)
            if cmd:
                break
        if not cmd:
            return ''
        if 'input' in cmd.execstr.lower():
            inputtype = 'input'
            m = re.search(r'type="(\w*)"', cmd.execstr, re.IGNORECASE)
            if not m:
                m = re.search(r'input(\w*)\("', cmd.execstr, re.IGNORECASE)
            if m:
                inputtype = m.groups()[0].lower()
                binding += f'[:45] {inputtype}[/]'

        helpstr = cmd.helpstr
        return f'[:keys]{binding}[/] ([:longname]{longname}[/]) to {helpstr}'


class GuideSheet(Sheet):
    rowtype = 'lines'
    filetype = 'guide'
    columns = [
            ItemColumn('linenum', 0, type=int, width=0),
            ItemColumn('guide', 1, width=80, displayer='full'),
            ]
    precious = False
    guide_text = ''
    sheettype = Sheet

    def iterload(self):
        winWidth = 78
        helper = AttrDict(commands=CommandHelpGetter(self.sheettype),
                          options=OptionHelpGetter())
        guidetext = MissingAttrFormatter().format(self.guide_text, help=helper, vd=vd)
        for startingLine, text in enumerate(guidetext.splitlines()):
            text = text.strip()
            if text:
                for i, (L, _) in enumerate(wraptext(str(text), width=winWidth)):
                    yield [startingLine+i+1, L]
            else:
                yield [startingLine+1, text]



@VisiData.api
def getGuide(vd, name): # -> GuideSheet()
    if name in vd.guides:
        return vd.guides[name]()
    vd.warning(f'no guide named {name}')

BaseSheet.addCommand('', 'open-guide-index', 'vd.push(GuideIndex("VisiData_Guide"))', 'open VisiData guides table of contents')

@VisiData.api
def inputKeys(vd, prompt):
    return vd.input(prompt, help=f'''
                # Input Keystrokes
                - Press `Ctrl+N` and then press another keystroke to spell out that keystroke.
                - Press `Ctrl+C` to cancel the input.
                - Press `Enter` to accept the input.
            ''')

@BaseSheet.api
def getCommandInfo(sheet, keys):
    cmd = sheet.getCommand(keys)
    return CommandHelpGetter(type(sheet))[cmd.longname]

vd.addCommand('', 'show-command-info', 'status(getCommandInfo(inputKeys("get command for keystrokes: ")))', 'show longname and helpstring for keybinding')

vd.addMenuItems('''
        Help > VisiData Feature Guides > open-guide-index
''')

vd.optalias('guides', 'preplay', 'open-guide-index')

vd.addGlobals({'GuideSheet':GuideSheet, "CommandHelpGetter": CommandHelpGetter, "OptionHelpGetter": OptionHelpGetter})
