# minimalist options framework

- getattr: use options.wait_time to get option value or assign with `options.wait_time = 50`
- getitem: options['wait_time'] will also work
- use '_' for word separator
- all options (except those that start `disp_` and `color_`) can be passed on the command-line
- options can be set in .visidatarc as simple Python
   - `options.wait_time = 50`
- but '_' gets converted to `-` when used as a command line arg (`--wait-time=50`)
