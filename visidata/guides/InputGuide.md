# Input keystrokes

When VisiData prompts for input — such as when opening a file or searching — a prompt appears at the bottom of the screen. The following keystrokes are available whenever that prompt is open.

## Submit and cancel

- `Enter` — accept input and run the command
- `Escape` or `Ctrl+C` — cancel input and return to the sheet

## Edit the input

- `Backspace` — delete the previous character
- `Ctrl+U` — clear the entire line
- `Ctrl+R` — reload the initial value
- `Ctrl+O` — open the input in an external editor (requires `$EDITOR` to be set)

## Move the cursor

- `Left`/`Right` — move one character
- `Ctrl+A` — move to the beginning of the line
- `Ctrl+E` — move to the end of the line

## History

- `Up`/`Down` — cycle through previous inputs for this prompt type

Each prompt type maintains its own history. Search history and filename history are stored separately.

## Autocomplete

- `Tab`/`Shift+Tab` — cycle through available completions (when available)
