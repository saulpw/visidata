- Update: 2018-01-22
- Version: VisiData 1.0

# Loading data

## How to specify a source

In VisiData, [loaders](/docs/loaders) load files of a particular type. The following [sources](/man#loaders) are currently supported.

On default, the file extension determines which loader is used. Unknown filetypes are loaded as **Text sheets**.

~~~
vd sample.tsv
~~~

To enforce usage of a particular loader pass the `-f` flag, along with the name of the loader.

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

Upon launching, the most recent dataset which was loaded (e.g. sunshinelist.html) will be displayed.

To load additional datasets from within a session, press `o` and enter a filepath.

---

## How to access other loaded or derived sheets:

1. Press `S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

---
