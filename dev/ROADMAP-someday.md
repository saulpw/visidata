# Maybe Someday

VisiData tasks that are looking for a lovely home!

These are tasks that are not on the immediate developer roadmap, and are looking for someone to take the lead on them. If any of them draw you in, and you would like to help drive their implementation, [open an issue](https://github.com/saulpw/visidata/issues/new) or reopen the linked issue.

- sniff filetype from the data itself: [issue](https://github.com/saulpw/visidata/issues/130)
    - detect utf16 byte-order-marker and set encoding: [issue](https://github.com/saulpw/visidata/issues/200)
- [loader] RSS reader: [issue](https://github.com/saulpw/visidata/issues/157)
- [loader] Frictionless Data Packages: [issue](https://github.com/saulpw/visidata/issues/237)
- [diff] expand --diff into a vdiff plugin: [issue](https://github.com/saulpw/visidata/issues/303)

- [ColumnsSheet] show subcolumns and their parent column (for expand/contract)

- [sheets] start/drop datetimes
   - [sheets] number of derivative sheets (two columns, for immediate children and to any depth)
   - [sheets] number of commands executed on that sheet (as a list so they can be viewed separately)

- [vsh](http://github.com/saulpw/vsh) (unreleased)
   - vtop (includes kill/killall/ps)
   - vls (rm/mv/cp/mount/find/grep/mkdir/rmdir/ln/touch)
   - vnet (netstat)
   - vping
   - vproc (explore /proc filesystem with some added goodies)
- vsql: interacts with remote sql databases; no loading required
- vpy: python explorer/debugger
- vchat: wechat with data features
- [vdgalcon](http://github.com/saulpw/vdgalcon)
- vscrape: point at a website and collect datasets, tables, textual data
- vapi: convenient interface to REST and other APIs
- vstats
   - save commandlog as ipynb, markdown, or html
- vaws
- `vd --server` pops up a local web server, for a visidata-like web interface to local files
