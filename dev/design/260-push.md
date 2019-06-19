- first push causes reload (self.rows is initially the UNLOADED sentinel)
- reload is usually async
- reload assigns a new object to .rows
- if you assign .rows after push, the reload thread may come by after and re-set it
- and maybe other members are reset by reload too
- so don't assign any members after reload (and thus push)
- api fix: vd.push no longer returns the sheet
- if you want it reloaded every push, call .reload() before the push

