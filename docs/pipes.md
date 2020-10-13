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
   - `ls|vd|lpr` to interactively select a list of filenames to send to the printer
      - Visdata without arguments will find all the files in the current directory including metadata (e.g. size, modtime, owner) so this can be said more simply as `vd | lpr`

Some useful commands to use when in a pipeline:
   - [ ] **how do we save the contents of one column without a header?**
   - [ ] **how do we convert output to a different format?**
   - `q`/`gq` to output nothing
   - `Ctrl+Q` to output current sheet (like at end of -b)
   - `vd -o-` to send directly to the terminal (not necessary if already redirected)
