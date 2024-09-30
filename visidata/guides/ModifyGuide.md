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

Modifying a sheet displays a `[M]` in the lower right status.

## Deferred Sheets

Some sheet types support *deferred* saving. Examples include **SQLiteSheet** and **Dir Sheet**. Changes are colored for [:add_pending]added rows[/], [:delete_pending]deleted rows[/], [:change_pending]modified cells[/].

Commit the sheet to reflect changes on the filesystem.

- {help.commands.commit_sheet}

### Relevant options

- {help.options.quitguard}

- {help.options.color_add_pending}
- {help.options.color_delete_pending}
- {help.options.color_change_pending}

