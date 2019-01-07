- Update: 2018-12-18
- Version: VisiData 1.5.1

# Loading data

## How to specify a source

In VisiData, a [loader](/docs/loaders) is a module which directs how VisiData structures and engages with a particular data source. [These sources](/man#loaders) are currently supported.

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

VisiData has an adapter for pandas. To load a file format which is supported by pandas, execute `vd -f pandas data.foo`. This will call `pandas.read_foo()`.

For example:

~~~
vd -f pandas data.parquet
~~~

loads a parquet file. When using the pandas loader, the `.fileformat` file extension is mandatory.

Note that if you are using Python v3.7, then you will need to manually install pandas >=0.23.2 (our requirements.txt file installs v0.19.2 as the last version compatible with 3.4).

---

## How to load multiple datasets simultaneously

Multiple files can be passed as inputs through the commandline.

~~~
vd birdsdiet.tsv surveys.csv sunshinelist.html
~~~

Upon launching, the final dataset to load (in this case, sunshinelist.html) will be displayed on top.

To load files from within a VisiData session, press `o` and enter a filepath.

---

## How to access other loaded or derived sheets:

1. Press `S` to open the **Sheets sheet**.
2. Move the cursor to the row containing the desired sheet.
3. Press `Enter` to jump to the sheet referenced in that current cursor row.

---

## [How to convert a dataset from one supported filetype into another](#convert) {#convert}

~~~
vd -b countries.fixed -o countries.tsv
~~~

**Note**: Not all filetypes which are supported as loaders are also supported as savers. See the [manpage](/man#loaders) for the supported output formats.


---
