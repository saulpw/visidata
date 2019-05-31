# modularity and extensibility

    Command('^P', 'open-statuses', 'vd.push(vd.statuses)')

    @VisiData.property
    def statuses(vd):
        'list of previous status messages'
        return StatusesSheet(name='statuses', source=vd.statuses)

Of note:

a) Core visidata objects are subclassed from Extensible
  - `@cached_property`
     - create on first use is necessary to avoid circular source dependencies
     - same sheet is pushed every time
  - `@property`
  - `@api`: a function on the VisiData singleton object
  - `@global_api`: a function on VisiData, that is also in the 'global' scope for convenient access (status, input, etc)
  - `init('member', constructor)`
    - BaseSheet.init('undone', list)


b) In these modular member functions, the first argument would normally be 'self'.  But as they are removed from the actual class definition it seems better to use a specific local object name: `vd`, `sheet`, 'col'.

c) every sheet needs a name and a source.  SomeSheet.reload() should know how to get the rows from the source.

d) `statuses` and its docstring will be shown on the Shift+V VisiData menu
  - open-X -> vd.X  
  - 

# naming and organization


## declarations
    globalCommand('^P', 'open-statuses', 'vd.push(vd.statusesSheet)')
    BaseSheet.Binding('^L', 'redraw')
    option('skip', 0, 'number of lines to skip in text files')
    theme('color_app_optname', 'default_color', 'when color applies')

## overrides
    SomeSheet.option('skip', 2)
    SomeSheet.theme('color_app_optname', 'overridden_color')

--

# Renames

## VisiData
    allPrefixes -> prefixes?
    allSheets -> sheets.rows
    clipboard() -> vd.clipboard
    clipcells -> vd.clipboard.clipcells
    cliprows -> vd.clipboard.cliprows
    globalOptionsSheet -> global_options?
    keystrokes -> _keystrokes
    lastErrors -> errors
    lastInputs -> inputs
    macrosheet -> macros
    mousereg -> _mousereg
    searchContext -> searches
    sheets -> sheetsSheet.rows (~40)
    sheetsSheet -> sheets
    statusHistory -> statuses?
    statuses -> _currentStatus?
    threads -> threadsSheet.rows
    threadsSheet -> threads
    unfinishedThreads -> threadsSheet.unfinished[Threads]
    windowWidth -> _width
    windowHeight -> _height

    globalCommand -> vd.addCommand
    BHQ: vd.addCommand -> vd.command?

    Sheet.addCommnd -> Sheet.command?
    Sheet.option() and vd.option()?
    Sheet.options for sure

    prev-sheet -> jump-prev

    urlcache(url=, days=)
    BaseSheet(name='')

    visidata.Path -> pathlib.Path

    id(row) -> Sheet.rowid

    helpstr -> help?

    Graph -> GraphSheet?
    Canvas -> CanvasSheet?

### Then VisiData would have:

    sheets       S
    cmdlog       D
    clipboard    B
    options      O
    errors       g Ctrl+E
    history      disabled
    inputs       
    macros       
    searches     
    statuses     Ctrl+P
    threads      Ctrl+T

    plugins

---
    and a sheet's metasheet would have:
    options      zO
    columns      C
    transposed   T
    melted       M

    pivot
    describe
    freq
    copy
    filter

## Column renames

[override these]
    calcValue -> realGetValue
        calls getter by default

     -> realSetValue actually modifies the row, and the backing data store depending on the sheet
       - data sheets don't do this internally, but the behavior is the same; ^S required for writing anything to disk

    getter/setter can be passed in to Sheet; the default realGetValue/realSetValue call them

[don't override these]
    getValue caches if column.cache=True
    setValue defers if column.defer=True

##

# topics

## `urlcache(url, days=1, encoding='utf-8'): Path`
   - convenient way to fetch a url while being polite to everyone's network connection
   - use Path like a file, because it is (was saved to disk first).  no streaming.
   - used by motd so is done every session
     - requests is great but an unnecessary dependency for this use
   - set encoding to None for binary objects
   - days=0 for no caching
- @asyncthread
   - threads must not have any user input (confirm, input, editText)

# Properties of visidata type classes

where T is the type class (like `int`, `date`, etc) and `v` is an instance of that type.

- callable
    - T(): (no value): a reasonable default value of this type
    - T(v): exact copy of value
    - T(str): converts from a reasonable string representation
-  `__name__`: shown in ColumnsSheet.type

# Properties of objects returned by T()

- comparable (for sorting)
- hashable
- roundable (for binning)
- formattable

# defType(): registers a type in the typemap
- .typetype: actual type class T above
- .icon: unicode character in column header
- .fmtstr: format string to use if fmtstr not given
- .formatter(fmtstr, typedvalue): formatting function (by default `locale.format_string` if fmtstr given, else `str`)

getType(T) -> vdtype

