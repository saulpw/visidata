# .vd files

`.vd` files are records of VisiData workflows, which can be run like scripts using the `--play` argument of `vd`.

To build a `.vd` file, run through a workflow and then press `Shift-D` to view the commandlog.
The commandlog can then be edited and then saved with `Ctrl-S`. Cells may be parameterized like `{foo}`, which can then be specified on the `vd --play` command-line as `--foo=value`. A commandlog can also be automatically saved with `Ctrl-D`. 

This folder contains the `.vd` files which are referenced for VisiData system tests.

