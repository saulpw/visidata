# How can I load files and exit the program?

If you use the command line, 'vd' should pretty much work as you expect:

        $ vd foo.csv

You can pipe in tabular data:

        $ find | vd

If the file is not plain ASCII .txt or [tsv](/tsv), you will have to specify the filetype with -f and/or other options:

        $ ls -al | vd -f fixed --skip 1 --headers 0

Many [data formats](/formats) are supported, with more being added every day.

# How do I quit?

You can just bang on 'q' until all the sheets are gone (there are usually only one or two anyway).

   Note: If a prompt or editbox is waiting for input, you may have to press '^C' first.

It requires a bit more dexterity, but Control-Q (aka '^Q') will abort the program quite rudely.[1]

If you wish to be a bit gentler, 'gq' will quit all sheets ('global quit').


[1] Control-Q is the only builtin command (necessary sometimes during development).  All other [commands can be overridden](/howto/commands).
