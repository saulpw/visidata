# Viewing two sheets simultaneously

VisiData supports the viewing of two sheets simultaneously with a feature called split screen.

## Entering split screen mode

Keystroke(s)        Action
------------        ------
`Shift+Z`           split screen in half, placing second sheet on stack visibly in the second pane
`z Shift+Z` *n*     split screen, setting the height of the second screen to *n*


When there is a single pane, all currently-open sheets are situated within the same sheets stack. The more recent that sheet was viewed, the higher it is in the [stack](https://jsvine.github.io/intro-to-visidata/basics/understanding-sheets/#how-to-use-the-sheets-sheet).

Split-pane opens a second window, and creates a second stack for it. This keeps the sheet stably within a specific window.

For instance, pressing `Shift+C` on the [sample.tsv]() will give us a stack with two columns, the sample **Sheet** and its **Columns Sheet**.

![]

Pressing `Shift+Z` will now give us a view of them both, with the sample **Sheet** moved to the second window.

![]

## Split screen mode specific commands

While in split screen mode, you can move between windows, adjust the sheets that appear in the current window, and full-screen the current pane.

Keystroke(s)        Action
------------        ------
`z Shift+Z` *n*     adjust the height of the second window to *n*
`g Shift+Z`         full screen the current window
`Tab`               make the other window the active window
`Ctrl+^`            swap top two sheets in stack in current window, second sheet in stack is now visible
`g Ctrl+^`          cycle through sheets in stack in current window

For instance, we can use `Tab` to make the sample **Sheet** the active window.

![]

Moving around it, we can see the **Columns Sheet** in the top window continuing to be updated.

We can press `Shift+F` on the **Item** column to view its [Frequency Table]().

Now, the visible sheet of the second window has changed, while the visible sheet on the top window has stayed the same.

![]

We can use `^^`, so that sample **Sheet** is once again visible, and full-screen it with `g Shift+Z`, effectively leaving split screen mode.

![]
