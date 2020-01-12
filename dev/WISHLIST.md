# Things we wish VisiData could do

## Installers

- .pkg for macos # 253
- .exe for windows
- snap for linux  #254

## core VisiData

### [aggregators] add percent-of-total columns with count/sum #274
- [expr] percentage columns `=x*100/sum(col('x'))`: [@agguser on issue #197](https://github.com/saulpw/visidata/issues/197#issuecomment-447923028):

### types

- [datetime] handle timezone
- [currency] track currency kind/symbol

### [FreqSheet] --follow option to continue grouping as new rows are loaded on the source sheet #366

- [sheets] start/drop datetimes
   - [sheets] number of derivative sheets (two columns, for immediate children and to any depth)
   - [sheets] number of commands executed on that sheet (as a list so they can be viewed separately)


### [Pivot] refactor/cleanup numeric binning for pivot table

## minor features

- [ColumnsSheet] show subcolumns and their parent column (for expand/contract)
- [color] gradients for numeric columns
- SI display format (1210000000 -> 1.21G)
- [regex] append "/flags" to regex commands for per-instance regex flags

## plugins and apps

These should all be implementable via the plugin framework.

### loaders and savers

- [loader] RSS reader: [#157](https://github.com/saulpw/visidata/issues/157)
- [google sheets] loader with savesToSource
- [hdf5] multisave_hdf5
- [canvas] Canvas.save_svg
- [ipybnb] Sheet.save_ipynb
- [sql] Sheet.save_sql

### extension for fmtstr that allows for {} type fmtstrs

### sniff filetype from the data itself ([#130](https://github.com/saulpw/visidata/issues/130))
    - ([#200](https://github.com/saulpw/visidata/issues/200)) detect utf16 byte-order-marker and set options.encoding

### `vd --server` pop up a local web server, for a visidata-like web interface to local files

### auto-join [common data lookups](https://github.com/wireservice/lookup)

### expand --diff into a vdiff plugin ([issue](https://github.com/saulpw/visidata/issues/303))

### make macros a proper plugin ([issue](https://github.com/saulpw/visidata/issues/431#issuecomment-573265659))

### [vsh](https://github.com/saulpw/visidata/tree/develop/vsh) (unreleased)
   - vtop (top/kill/killall/ps)
   - vls (rm/mv/cp/mount/find/grep/mkdir/rmdir/ln/touch)
      [vls] archive/extract (zip/unzip and relatives)
   - vnet (netstat)
   - vping
   - vproc (explore /proc filesystem with some added goodies)

### vsql: interacts with remote sql databases; no loading required

### vpy: python explorer/debugger

### vchat: wechat with data features

### [vdgalcon](http://github.com/saulpw/vdgalcon)

### vscrape: point at a website and collect datasets, tables, textual data

### vapi: convenient interface to REST and other APIs
   - http://json-schema.org/specification.html
   - https://brandur.org/elegant-apis

### vstats
   - save commandlog as ipynb, markdown, or html

### vaws

### vgeo

   - spatialite #291

