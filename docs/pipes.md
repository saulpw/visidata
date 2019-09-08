- Update: 2019-09-11
- Version: VisiData 2.0

# STDOUT pipe/redirect

Visdata is pipe-friendly, and can work with other tools in a pipeline.  Visidata can interactively filter stdin, and save to stdout.
  - Use it to manually update tabular data in a pipeline  `mysql < query.sql | vd | awk 'awkity {awk}'
  -
You can use it edit 




    - `ls|vd|lpr` to interactively select a list of filenames to send to the printer
    - `q`/`gq` to output nothing
    - `Ctrl+Q` to output current sheet (like at end of -b)
    - `vd -o-` to send directly to the terminal (not necessary if already redirected)
