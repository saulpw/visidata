# getting input from the user

    VisiData.input(prompt, type=None, defaultLast=False, history=[], dy=0, attr=None, updater=lambda v: None, **editargs) -> str:
      - get a line of input from the user on the status line
      - history stored and managed by 'type' if given
      - defaults to last history item if no input and defaultLast is True
      - updater(val) is called on every keypress or timeout
      - dy: number of lines from bottom of pane; attr: curses attribute for prompt
      - see the docstring in _input.py for the rest (display, record, bindings, help)


    VisiData.confirm(prompt, exc=EscapeException) -> bool or raise:
      - if input is not 'y', raise exc (or returns False if exc=None)
      - input not recorded on cmdlog

    VisiData.choose(choices, n=None, type='') -> key or list of keys:
      - choices is a list of dicts, each with a unique "key"
      - keys typed separated by spaces, or picked from a ChoiceSheet in fancy mode (see chooseMany)

    Sheet.editCell(vcolidx, rowidx, **editargs) -> str:
      - edit a cell value in-place on the screen
      - return value converted to column type

# editargs

## `completer`

The `completer` editarg can be a callable `func(value:str, state:int) -> str:` which takes the current value up to the cursor, and a numeric "state" which basically indicates the number of times the user has pressed `Tab` from this exact position (possibly negative with Shift-Tab).  It returns the potential completion value for that state.

## `history`

can be either a list of strings (previous inputs) or a string indicating type
