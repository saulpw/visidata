- Update: 2019-09-11
- Version: VisiData 2.0

# STDOUT pipe/redirect

Visdata is pipe-friendly, it works well with other tools in a pipeline.  Visidata can interactively filter stdin, and save the
results to stdout.

Visidata shines over other pickers like fzf with the ability to select a line based on values other than
the name of the items being selected.   Visidata understands numeric and date values. Visidata can
sort by file size,  sort processes by memory usage, or last modification times.  By first sorting by
this metadata, it can be easier to find what file or process you want to choose.


   - Use it to manually update (sort, filter, edit) tabular data in a pipeline  `mysql < query.sql | vd | awk 'awkity {awk}'
   - Use to interactively pick processes to kill `ps -ef | vd | tail -n +2 | xargs --no-run-if-empty kill`
   - `ls|vd|lpr` to interactively select a list of filenames to send to the printer
   - **how do we save the contents of one column without a header?**
   - **how do we convert output to a different format?*"
   - `q`/`gq` to output nothing
   - `Ctrl+Q` to output current sheet (like at end of -b)
   - `vd -o-` to send directly to the terminal (not necessary if already redirected)
