'''
# A Guide to VisiData Guides
Each guide shows you how to use a particular feature in VisiData.

  [:keys]Up/Down[/] to move the row cursor
  [:keys]Enter[/] to view a topic
  [:keys]Backspace[/] to come back to this list of guides
'''

import re

from visidata import vd, BaseSheet, Sheet, ItemColumn, Column, VisiData


@VisiData.api
class GuideGuide(Sheet):
    help = __doc__
    columns = [
        ItemColumn('n', 0, type=int),
        ItemColumn('sheetname', 1, width=0),
        ItemColumn('topic', 2, width=60),
        Column('points', type=int, getter=lambda c,r: 0),
        Column('max_points', type=int, getter=lambda c,r: 100),
    ]
    def iterload(self):
        i = 0
        for line in '''
GuideGuide ("A Guide to VisiData Guides (you are here)")
HelpGuide ("Where to Start and How to Quit")  # manpage; ask for patreon
MenuGuide ("The VisiData Menu System")
CommandsSheet ("How to find the command you want run")

#  real barebones basics
MovementGuide ("Movement and Search")
SortGuide ("Sorting")
TypesSheet ("The basic type system")
CommandLog  ("Undo and Replay")

#  rev this thing up

SelectionGuide ("Selecting and filtering") # stu|, and variants; filtering with dup-sheet; g prefix often refers to selected rowset
SheetsSheet  ("The Sheet Stack")
ColumnsSheet ("Columns: the only way to fly")
StatusesSheet ("Revisit old status messages")
SidebarSheet ("Dive into the sidebar")
SaversGuide ("Saving Data")

ErrorsSheet ("What was that error?")
ModifyGuide ("Adding, Editing, Deleting Rows")

# the varieties of data experience

SlideGuide ("Sliding rows and columns around")
ExprGuide ("Compute Python over every row")
JoinGuide ("Joining multiple sheets together")
DescribeSheet ("Basic Statistics (min/max/mode/median/mean)")
AggregatorsSheet ("Aggregations like sum, mean, and ")
FrequencyTable ("Frequency Tables are how you GROUP BY")
PivotGuide ("Pivot Tables are just Frequency Tables with more columns")
MeltGuide ("Melt is just Unpivot")
JsonGuide ("Some special features for JSON") # with expand/contract, unfurl
RegexGuide ("Matching and Transforming Strings with Regex")
GraphSheet ("Basic scatterplots and other graphs")

# for the frequent user
OptionsSheet ("Options and Settings")
ClipboardGuide ("Copy and Paste Data via the Clipboard")
DirSheet ("Browsing the local filesystem")
FormatsSheet ("What can you open with VisiData?")
ThemesSheet ("Change Interface Theme")
ColorSheet ("See available colors")
MacrosSheet ("Recording macros")
MemorySheet ("Making note of certain values")

# advanced usage and developers

ThreadsSheet ("Threads past and present")
PyobjSheet ("Inspecting internal Python objects")

#  appendices

InputEditorGuide ("Using the builtin line editor")
        '''.splitlines():
            m = re.search(r'(\w+?) \("(.*)"\)', line)
            if m:
                yield [i] + list(m.groups())
                i += 1

BaseSheet.addCommand('', 'open-guide', 'vd.push(GuideGuide("VisiData_Guide"))')
