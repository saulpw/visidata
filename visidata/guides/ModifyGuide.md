# Adding, Editing, Deleting Rows

In addition to cutting and pasting (see **Clipboard Guide**), rows can be created from scratch, edited and deleted.

- {help.commands.add-row}
- {help.commands.add-rows}

- {help.commands.delete-row}
- {help.commands.delete-selected}

- {help.commands.sysedit-selected}
- {help.commands.edit_cell}

While editing a cell, press `Ctrl+G` to cycle through the sidebar guides to see the **Input Keystroke Help**.

A sample of available commands:
    - [:code]Ctrl+O[/] to edit the cell in a text editor.
    - [:code]Tab[/] to finish editing and go to the next cell
    - [:code]Shift+Tab[/] to finish editing and go to the previous cell

## Deferred Sheets

Some sheet types support *deferred* saving. Examples include **SQLiteSheet** and **Dir Sheet**. Modifications are colored: green for added rows, red for deleted rows, and yellow for modified cells.

Commit the sheet to reflect changes on the filesystem.

- {help.commands.commit_sheet}



