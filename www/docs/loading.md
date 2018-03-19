- Update: 2018-01-28
- Version: VisiData 1.0

# Loading data

## How to specify a source

In VisiData, [loaders](/docs/loaders) load files of a particular type. [These sources are currently supported](/man#loaders).

On default, the file extension determines which loader is used. Unknown filetypes are loaded as **Text sheets**.

~~~
vd sample.tsv
ps aux | vd
~~~

To force a particular loader, pass `-f` with the filetype or format name.

~~~
vd -f sqlite bar.db
ls -l | vd -f fixed
~~~

---

## How to load multiple datasets simultaneously

Multiple files can be passed as inputs through the commandline.

~~~
vd birdsdiet.tsv surveys.csv sunshinelist.html
~~~

Upon launching, the last dataset to load (in this case, sunshinelist.html) will be displayed on top.

To load another file, press `o` and enter a filepath.

---

## How to access other loaded or derived sheets:

1. Press `S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

## How to convert a dataset from one supported filetype into another

~~~
vd -b countries.fixed -o countries.tsv
~~~

**Note**: Not all filetypes which are supported as loaders are also supported as savers. See the [manpage](/man#loaders) for the supported output formats.


---
