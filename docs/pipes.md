---
eleventyNavigation:
   key: Pipes
   order: 14
Update: 2019-09-11
Version: VisiData 2.0
---


## stdin/stdout pipe/redirect

VisiData works with other tools in a pipeline. VisiData will read any piped input from stdin as a sheet, and save the
results of any remaining sheets to stdout Visdata allows interactive edits in the middle of a pipeline.

   - Use it to manually update (sort, filter, edit) tabular data in a pipeline  `mysql < query.sql | vd | awk 'awkity {awk}'
   - Use it to interactively pick processes to kill `ps -ef | vd | tail -n +2 | xargs --no-run-if-empty kill`

When redirecting VisiData output:

   - `Ctrl+Q` will output current sheet (as it quits with the top sheet still on the stack)
   - `q` (or `gq`) will output nothing (as it quits by dropping all sheets from the stack)

Use `vd -o-` to send directly to the terminal when not redirecting stdout (it's not necessary if already redirected).

To output a single column without the column header, make sure only that column is visible and save as .txt.  For example, `vd . --save-filetype txt | lpr`.
