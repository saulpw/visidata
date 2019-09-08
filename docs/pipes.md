- Update: 2019-09-11
- Version: VisiData 2.0

# STDOUT pipe/redirect

Visdata is pipe-friendly, working well with other tools in a pipeline.  Visidata can interactively filter stdin, and save the results to stdout.
Visidata  is easier to use than other interactive pickers, when you want to search or filter on criteria other than just the name of the items, like filesize,
Process memory size or owner, network usage.

   - Use it to manually update tabular data in a pipeline  `mysql < query.sql | vd | awk 'awkity {awk}'
   - Use to interactively pick processes to kill `ps -ef | vd | xargs -r kill`
   - `ls|vd|lpr` to interactively select a list of filenames to send to the printer
   - **how do we save the contents of one column without a header?**
   - **how do we convert output to a different format?*"
   - `q`/`gq` to output nothing
   - `Ctrl+Q` to output current sheet (like at end of -b)
   - `vd -o-` to send directly to the terminal (not necessary if already redirected)
