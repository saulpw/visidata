# getting input from the user

    VisiData.input(prompt, type='', defaultLast=False, **editargs) -> str:
      - get a line of input from the user on the status line
      - history stored and managed by 'type' if given
      - defaults to last history item if no input and defaultLast is True


    VisiData.confirm(prompt, exc=ExpectedException) -> bool or raise:
      - if input is not 'y', raise esc (or returns False if exc=None)
      - input not recorded on cmdlog

    VisiData.choose(L:Sequence, n=None) -> element or list:
      - input choices separated by spaces.  may have a better interface eventually.

    Sheet.edit(col, row, **editargs) -> str:
      - edit a cell value in-place on the screen
      - return value converted to column type

# editargs

## `completer`

The `completer` editarg can be a callable `func(value:str, state:int) -> str:` which takes the current value up to the cursor, and a numeric "state" which basically indicates the number of times the user has pressed `Tab` from this exact position (possibly negative with Shift-Tab).  It returns the potential completion value for that state.

## `history`

can be either a list of strings (previous inputs) or a string indicating type
