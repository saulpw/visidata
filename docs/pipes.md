- Update: 2019-09-11
- Version: VisiData 2.0

# STDOUT pipe/redirect

Visdata is pipe-friendly, it works well with other tools in a pipeline.  Visidata can interactively filter stdin, and save the
results to stdout.

Visdata is more convenient than standard Unix filtering commands because it allows interactive edits in the middle of a pipeline.
Visidata shines over other pickers like `fzf` with the ability to select lines based on values other than
the name of the items being selected.  Visidata understands numeric, date, currency, and custom values.  Visidata can
sort by file size, sort processes by memory usage, or last modification times.  By first sorting or filtering by
this metadata, you can more easily find what file(s) or process(es) you want to choose.

   - Use it to manually update (sort, filter, edit) tabular data in a pipeline  `mysql < query.sql | vd | awk 'awkity {awk}'
   - Use it to interactively pick processes to kill `ps -ef | vd | tail -n +2 | xargs --no-run-if-empty kill`

When redirecting VisiData output:

   - `Ctrl+Q` will output current sheet (as it quits with the top sheet still on the stack)
   - `q` (or `gq`) will output nothing (as it quits by dropping all sheets from the stack)

Use `vd -o-` to send directly to the terminal when not redirecting stdout (it's not necessary if already redirected).

To output a single column without the column header, make sure only that column is visible and save as .txt.  For example, `vd . --save-filetype txt | lpr`.
