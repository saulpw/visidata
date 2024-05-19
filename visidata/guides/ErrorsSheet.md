# What was that error?

Status messages include [:warning]warnings[/] and [:error]errors[/].

A command may issue a [:warning]warning[/] status and continue running.
A command that [:warning]fails[/] or [:error]errors[/] is aborted.

## Investigating errors further

If a Python Exception like [:error]RuntimeError[/] appears in the sidebar:

- {help.commands.error_recent}
- {help.commands.errors_all}

If [:note_type]{vd.options.disp_note_fmtexc}[/] or [:error]{vd.options.disp_note_getexc}[/] appear inside a cell, it indicates an error happened during calculation, type-conversion, or formatting.  When the cursor is on an error cell:

- {help.commands.error_cell}
