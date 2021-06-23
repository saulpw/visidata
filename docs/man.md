---
title: Quick Reference Guide
permalink: /man/
---
<pre id="manpage" class="whitespace-pre-wrap text-xs">
vd(1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        Quick Reference Guide                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        vd(1)

<span style="font-weight:bold;">NAME</span>
     <span style="font-weight:bold;">VisiData</span> — a terminal utility for exploring and arranging tabular data

<span style="font-weight:bold;">SYNOPSIS</span>
     <span style="font-weight:bold;">vd</span> [<span style="text-decoration:underline;">options</span>] [<span style="text-decoration:underline;">input</span> ...]
     <span style="font-weight:bold;">vd</span> [<span style="text-decoration:underline;">options</span>] <span style="font-weight:bold;">--play</span> <span style="text-decoration:underline;">cmdlog</span> [<span style="font-weight:bold;">-w</span> <span style="text-decoration:underline;">waitsecs</span>] [<span style="font-weight:bold;">--batch</span>] [<span style="font-weight:bold;">-o</span> <span style="text-decoration:underline;">output</span>] [<span style="text-decoration:underline;">field</span><span style="font-weight:bold;">=</span><span style="text-decoration:underline;">value</span>]
     <span style="font-weight:bold;">vd</span> [<span style="text-decoration:underline;">options</span>] [<span style="text-decoration:underline;">input</span> ...] <span style="font-weight:bold;">+</span><span style="text-decoration:underline;">toplevel</span>:<span style="text-decoration:underline;">subsheet</span>:<span style="text-decoration:underline;">col</span>:<span style="text-decoration:underline;">row</span>

<span style="font-weight:bold;">DESCRIPTION</span>
     <span style="font-weight:bold;">VisiData</span> is an easy-to-use multipurpose tool to explore, clean, edit, and restructure data. Rows can be selected, filtered, and grouped; columns can be rearranged, transformed, and derived via regex or Python expressions; and workflows can be saved, documented, and replayed.

   <span style="font-weight:bold;">REPLAY</span> <span style="font-weight:bold;">MODE</span>
     <span style="font-weight:bold;">-p</span>, <span style="font-weight:bold;">--play</span>=<span style="text-decoration:underline;">cmdlog</span>       replay a saved <span style="text-decoration:underline;">cmdlog</span> within the interface
     <span style="font-weight:bold;">-w</span>, <span style="font-weight:bold;">--replay-wait</span>=<span style="text-decoration:underline;">seconds</span>
                             wait <span style="text-decoration:underline;">seconds</span> between commands
     <span style="font-weight:bold;">-b</span>, <span style="font-weight:bold;">--batch</span>             replay in batch mode (with no interface)
     <span style="font-weight:bold;">-o</span>, <span style="font-weight:bold;">--output</span>=<span style="text-decoration:underline;">file</span>       save final visible sheet to <span style="text-decoration:underline;">file</span> as .tsv
     <span style="font-weight:bold;">--replay-movement</span>       toggle <span style="font-weight:bold;">--play</span> to move cursor cell-by-cell
     <span style="text-decoration:underline;">field</span><span style="font-weight:bold;">=</span><span style="text-decoration:underline;">value</span>             replace &quot;{<span style="text-decoration:underline;">field</span>}&quot; in <span style="text-decoration:underline;">cmdlog</span> contents with <span style="text-decoration:underline;">value</span>

   <span style="font-weight:bold;">Commands</span> <span style="font-weight:bold;">During</span> <span style="font-weight:bold;">Replay</span>
        <span style="font-weight:bold;">^U</span>                   pause/resume replay
        <span style="font-weight:bold;">^N</span>                   execute next row in replaying sheet
        <span style="font-weight:bold;">^K</span>                   cancel current replay

   <span style="font-weight:bold;">GLOBAL</span> <span style="font-weight:bold;">COMMANDS</span>
     All keystrokes are case sensitive. The <span style="font-weight:bold;">^</span> prefix is shorthand for <span style="font-weight:bold;">Ctrl</span>.

   <span style="font-weight:bold;">Keystrokes</span> <span style="font-weight:bold;">to</span> <span style="font-weight:bold;">start</span> <span style="font-weight:bold;">off</span> <span style="font-weight:bold;">with</span>
      <span style="font-weight:bold;">^Q</span>              abort program immediately
      <span style="font-weight:bold;">^C</span>              cancel user input or abort all async threads on current sheet
     <span style="font-weight:bold;">g^C</span>              abort all secondary threads
       <span style="font-weight:bold;">q</span>              quit current sheet
      <span style="font-weight:bold;">gq</span>              quit all sheets (clean exit)

      <span style="font-weight:bold;">^H</span>              view this man page
     <span style="font-weight:bold;">z^H</span>              view sheet of command longnames and keybindings
     <span style="font-weight:bold;">Space</span> <span style="text-decoration:underline;">longname</span>   execute command by its <span style="text-decoration:underline;">longname</span>

       <span style="font-weight:bold;">U</span>              undo the most recent modification (requires enabled <span style="font-weight:bold;">options.undo</span>)
       <span style="font-weight:bold;">R</span>              redo the most recent undo (requires enabled <span style="font-weight:bold;">options.undo</span>)

   <span style="font-weight:bold;">Cursor</span> <span style="font-weight:bold;">Movement</span>
     <span style="font-weight:bold;">Arrow</span> <span style="font-weight:bold;">PgUp</span> <span style="font-weight:bold;">Home</span>  go as expected
      <span style="font-weight:bold;">h</span>   <span style="font-weight:bold;">j</span>   <span style="font-weight:bold;">k</span>   <span style="font-weight:bold;">l</span>   go left/down/up/right
     <span style="font-weight:bold;">gh</span>  <span style="font-weight:bold;">gj</span>  <span style="font-weight:bold;">gk</span>  <span style="font-weight:bold;">gl</span>   go all the way to the left/bottom/top/right of sheet
          <span style="font-weight:bold;">G</span>  <span style="font-weight:bold;">gg</span>       go all the way to the bottom/top of sheet
     <span style="font-weight:bold;">^B</span>  <span style="font-weight:bold;">^F</span>           scroll one page back/forward
     <span style="font-weight:bold;">zz</span>               scroll current row to center of screen

     <span style="font-weight:bold;">^^</span> (Ctrl+^)      jump to previous sheet (swaps with current sheet)

      <span style="font-weight:bold;">/</span>   <span style="font-weight:bold;">?</span> <span style="text-decoration:underline;">regex</span>     search for <span style="text-decoration:underline;">regex</span> forward/backward in current column
     <span style="font-weight:bold;">g/</span>  <span style="font-weight:bold;">g?</span> <span style="text-decoration:underline;">regex</span>     search for <span style="text-decoration:underline;">regex</span> forward/backward over all visible columns
     <span style="font-weight:bold;">z/</span>  <span style="font-weight:bold;">z?</span> <span style="text-decoration:underline;">expr</span>      search by Python <span style="text-decoration:underline;">expr</span> forward/backward in current column (with column names as variables)
      <span style="font-weight:bold;">n</span>   <span style="font-weight:bold;">N</span>           go to next/previous match from last regex search

      <span style="font-weight:bold;">&lt;</span>   <span style="font-weight:bold;">&gt;</span>           go up/down current column to next value
     <span style="font-weight:bold;">z&lt;</span>  <span style="font-weight:bold;">z&gt;</span>           go up/down current column to next null value
      <span style="font-weight:bold;">{</span>   <span style="font-weight:bold;">}</span>           go up/down current column to next selected row

      <span style="font-weight:bold;">c</span> <span style="text-decoration:underline;">regex</span>         go to next column with name matching <span style="text-decoration:underline;">regex</span>
      <span style="font-weight:bold;">r</span> <span style="text-decoration:underline;">regex</span>         go to next row with key matching <span style="text-decoration:underline;">regex</span>
     <span style="font-weight:bold;">zc</span>  <span style="font-weight:bold;">zr</span> <span style="text-decoration:underline;">number</span>    go to column/row <span style="text-decoration:underline;">number</span> (0-based)

      <span style="font-weight:bold;">H</span>   <span style="font-weight:bold;">J</span>   <span style="font-weight:bold;">K</span>   <span style="font-weight:bold;">L</span>   slide current row/column left/down/up/right
     <span style="font-weight:bold;">gH</span>  <span style="font-weight:bold;">gJ</span>  <span style="font-weight:bold;">gK</span>  <span style="font-weight:bold;">gL</span>   slide current row/column all the way to the left/bottom/top/right of sheet
     <span style="font-weight:bold;">zH</span>  <span style="font-weight:bold;">zJ</span>  <span style="font-weight:bold;">zK</span>  <span style="font-weight:bold;">zK</span> <span style="text-decoration:underline;">number</span>
                      slide current row/column <span style="text-decoration:underline;">number</span> positions to the left/down/up/right

     <span style="font-weight:bold;">zh</span>  <span style="font-weight:bold;">zj</span>  <span style="font-weight:bold;">zk</span>  <span style="font-weight:bold;">zl</span>   scroll one left/down/up/right

   <span style="font-weight:bold;">Column</span> <span style="font-weight:bold;">Manipulation</span>
       <span style="text-decoration:underline;">_</span> (underscore)
                      toggle width of current column between full and default width
      <span style="font-weight:bold;">g</span><span style="text-decoration:underline;">_</span>              toggle widths of all visible columns between full and default width
      <span style="font-weight:bold;">z</span><span style="text-decoration:underline;">_</span> <span style="text-decoration:underline;">number</span>       adjust width of current column to <span style="text-decoration:underline;">number</span>
     <span style="font-weight:bold;">gz</span><span style="text-decoration:underline;">_</span> <span style="text-decoration:underline;">number</span>       adjust widths of all visible columns to Ar number

      <span style="font-weight:bold;">-</span> (hyphen)      hide current column
     <span style="font-weight:bold;">z-</span>               reduce width of current column by half
     <span style="font-weight:bold;">gv</span>               unhide all columns

     <span style="font-weight:bold;">!</span> <span style="font-weight:bold;">z!</span>             toggle/unset current column as a key column
     <span style="font-weight:bold;">~</span>  <span style="font-weight:bold;">#</span>  <span style="font-weight:bold;">%</span>  <span style="font-weight:bold;">$</span>  <span style="font-weight:bold;">@</span>  <span style="font-weight:bold;">z#</span>
                      set type of current column to str/int/float/currency/date/len
       <span style="font-weight:bold;">^</span>              edit name of current column
      <span style="font-weight:bold;">g^</span>              set names of all unnamed visible columns to contents of selected rows (or current row)
      <span style="font-weight:bold;">z^</span>              set name of current column to combined contents of current cell in selected rows (or current row)
     <span style="font-weight:bold;">gz^</span>              set name of all visible columns to combined contents of current column for selected rows (or current row)

       <span style="font-weight:bold;">=</span> <span style="text-decoration:underline;">expr</span>         create new column from Python <span style="text-decoration:underline;">expr</span>, with column names, and attributes, as variables
      <span style="font-weight:bold;">g=</span> <span style="text-decoration:underline;">expr</span>         set current column for selected rows to result of Python <span style="text-decoration:underline;">expr</span>
     <span style="font-weight:bold;">gz=</span> <span style="text-decoration:underline;">expr</span>         set current column for selected rows to the items in result of Python sequence <span style="text-decoration:underline;">expr</span>
      <span style="font-weight:bold;">z=</span> <span style="text-decoration:underline;">expr</span>         evaluate Python expression on current row and set current cell with result of Python <span style="text-decoration:underline;">expr</span>

       i (iota)       add column with incremental values
      gi              set current column for selected rows to incremental values
      zi <span style="text-decoration:underline;">step</span>         add column with values at increment <span style="text-decoration:underline;">step</span>
     gzi <span style="text-decoration:underline;">step</span>         set current column for selected rows at increment <span style="text-decoration:underline;">step</span>

      <span style="font-weight:bold;">'</span> (tick)        add a frozen copy of current column with all cells evaluated
     <span style="font-weight:bold;">g'</span>               open a frozen copy of current sheet with all visible columns evaluated
     <span style="font-weight:bold;">z'</span>  <span style="font-weight:bold;">gz'</span>          add/reset cache for current/all visible column(s)

      <span style="font-weight:bold;">:</span> <span style="text-decoration:underline;">regex</span>         add new columns from <span style="text-decoration:underline;">regex</span> split; number of columns determined by example row at cursor
      <span style="font-weight:bold;">;</span> <span style="text-decoration:underline;">regex</span>         add new columns from capture groups of <span style="text-decoration:underline;">regex</span> (also requires example row)
     <span style="font-weight:bold;">z;</span> <span style="text-decoration:underline;">expr</span>          create new column from bash <span style="text-decoration:underline;">expr</span>, with <span style="font-weight:bold;">$</span>columnNames as variables
      <span style="font-weight:bold;">*</span> <span style="text-decoration:underline;">regex</span><span style="font-weight:bold;">/</span><span style="text-decoration:underline;">subst</span>   add column derived from current column, replacing <span style="text-decoration:underline;">regex</span> with <span style="text-decoration:underline;">subst</span> (may include <span style="font-weight:bold;">\1</span> backrefs)
     <span style="font-weight:bold;">g*</span>  <span style="font-weight:bold;">gz*</span> <span style="text-decoration:underline;">regex</span><span style="font-weight:bold;">/</span><span style="text-decoration:underline;">subst</span>
                      modify selected rows in current/all visible column(s), replacing <span style="text-decoration:underline;">regex</span> with <span style="text-decoration:underline;">subst</span> (may include <span style="font-weight:bold;">\1</span> backrefs)

      <span style="font-weight:bold;">(</span>   <span style="font-weight:bold;">g(</span>          expand current/all visible column(s) of lists (e.g. <span style="font-weight:bold;">[3]</span>) or dicts (e.g. <span style="font-weight:bold;">{3}</span>) fully
     <span style="font-weight:bold;">z(</span>  <span style="font-weight:bold;">gz(</span> <span style="text-decoration:underline;">depth</span>    expand current/all visible column(s) of lists (e.g. <span style="font-weight:bold;">[3]</span>) or dicts (e.g. <span style="font-weight:bold;">{3}</span>) to given <span style="text-decoration:underline;">depth</span> (<span style="text-decoration:underline;">0</span>= fully)
      <span style="font-weight:bold;">)</span>               unexpand current column; restore original column and remove other columns at this level
     <span style="font-weight:bold;">zM</span>               row-wise expand current column of lists (e.g. <span style="font-weight:bold;">[3]</span>) or dicts (e.g. <span style="font-weight:bold;">{3}</span>) within that column

   <span style="font-weight:bold;">Row</span> <span style="font-weight:bold;">Selection</span>
       <span style="font-weight:bold;">s</span>   <span style="font-weight:bold;">t</span>   <span style="font-weight:bold;">u</span>      select/toggle/unselect current row
      <span style="font-weight:bold;">gs</span>  <span style="font-weight:bold;">gt</span>  <span style="font-weight:bold;">gu</span>      select/toggle/unselect all rows
      <span style="font-weight:bold;">zs</span>  <span style="font-weight:bold;">zt</span>  <span style="font-weight:bold;">zu</span>      select/toggle/unselect all rows from top to cursor
     <span style="font-weight:bold;">gzs</span> <span style="font-weight:bold;">gzt</span> <span style="font-weight:bold;">gzu</span>      select/toggle/unselect all rows from cursor to bottom
      <span style="font-weight:bold;">|</span>   <span style="font-weight:bold;">\</span> <span style="text-decoration:underline;">regex</span>     select/unselect rows matching <span style="text-decoration:underline;">regex</span> in current column
     <span style="font-weight:bold;">g|</span>  <span style="font-weight:bold;">g\</span> <span style="text-decoration:underline;">regex</span>     select/unselect rows matching <span style="text-decoration:underline;">regex</span> in any visible column
     <span style="font-weight:bold;">z|</span>  <span style="font-weight:bold;">z\</span> <span style="text-decoration:underline;">expr</span>      select/unselect rows matching Python <span style="text-decoration:underline;">expr</span> in any visible column
      <span style="font-weight:bold;">,</span> (comma)       select rows matching display value of current cell in current column
     <span style="font-weight:bold;">g,</span>               select rows matching display value of current row in all visible columns
     <span style="font-weight:bold;">z,</span> <span style="font-weight:bold;">gz,</span>           select rows matching typed value of current cell/row in current column/all visible columns

   <span style="font-weight:bold;">Row</span> <span style="font-weight:bold;">Sorting/Filtering</span>
       <span style="font-weight:bold;">[</span>    <span style="font-weight:bold;">]</span>         sort ascending/descending by current column; replace any existing sort criteria
      <span style="font-weight:bold;">g[</span>   <span style="font-weight:bold;">g]</span>         sort ascending/descending by all key columns; replace any existing sort criteria
      <span style="font-weight:bold;">z[</span>   <span style="font-weight:bold;">z]</span>         sort ascending/descending by current column; add to existing sort criteria
     <span style="font-weight:bold;">gz[</span>  <span style="font-weight:bold;">gz]</span>         sort ascending/descending by all key columns; add to existing sort criteria
      <span style="font-weight:bold;">&quot;</span>               open duplicate sheet with only selected rows
     <span style="font-weight:bold;">g&quot;</span>               open duplicate sheet with all rows
     <span style="font-weight:bold;">gz&quot;</span>              open duplicate sheet with deepcopy of selected rows

   <span style="font-weight:bold;">Editing</span> <span style="font-weight:bold;">Rows</span> <span style="font-weight:bold;">and</span> <span style="font-weight:bold;">Cells</span>
       <span style="font-weight:bold;">a</span>   <span style="font-weight:bold;">za</span>         append blank row/column; appended columns cannot be copied to clipboard
      <span style="font-weight:bold;">ga</span>  <span style="font-weight:bold;">gza</span> <span style="text-decoration:underline;">number</span>  append <span style="text-decoration:underline;">number</span> blank rows/columns
       <span style="font-weight:bold;">d</span>   <span style="font-weight:bold;">gd</span>         delete current/selected row(s)
       <span style="font-weight:bold;">y</span>   <span style="font-weight:bold;">gy</span>         yank (copy) current/all selected row(s) to clipboard in <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span>
      <span style="font-weight:bold;">zy</span>  <span style="font-weight:bold;">gzy</span>         yank (copy) contents of current column for current/selected row(s) to clipboard in <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span>
      <span style="font-weight:bold;">zd</span>  <span style="font-weight:bold;">gzd</span>         set contents of current column for current/selected row(s) to <span style="font-weight:bold;">options.null</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">value</span>
       <span style="font-weight:bold;">p</span>    <span style="font-weight:bold;">P</span>         paste clipboard rows after/before current row
      <span style="font-weight:bold;">zp</span>  <span style="font-weight:bold;">gzp</span>         set cells of current column for current/selected row(s) to last clipboard value
       <span style="font-weight:bold;">Y</span>   <span style="font-weight:bold;">gY</span>         yank (copy) current/all selected row(s) to system clipboard (using <span style="font-weight:bold;">options.clipboard</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">copy</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">cmd</span>)
      <span style="font-weight:bold;">zY</span>  <span style="font-weight:bold;">gzY</span>         yank (copy) contents of current column for current/selected row(s) to system clipboard (using <span style="font-weight:bold;">options.clipboard</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">copy</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">cmd</span>)
       <span style="font-weight:bold;">f</span>              fill null cells in current column with contents of non-null cells up the current column
       <span style="font-weight:bold;">e</span> <span style="text-decoration:underline;">text</span>         edit contents of current cell
      <span style="font-weight:bold;">ge</span> <span style="text-decoration:underline;">text</span>         set contents of current column for selected rows to <span style="text-decoration:underline;">text</span>

     <span style="font-weight:bold;">Commands</span> <span style="font-weight:bold;">While</span> <span style="font-weight:bold;">Editing</span> <span style="font-weight:bold;">Input</span>
        <span style="font-weight:bold;">Enter</span>  <span style="font-weight:bold;">^C</span>        accept/abort input
        <span style="font-weight:bold;">^O</span>               open external $EDITOR to edit contents
        <span style="font-weight:bold;">^R</span>               reload initial value
        <span style="font-weight:bold;">^A</span>  <span style="font-weight:bold;">^E</span>           go to beginning/end of line
        <span style="font-weight:bold;">^B</span>  <span style="font-weight:bold;">^F</span>           go back/forward one character
        <span style="font-weight:bold;">^←</span>  <span style="font-weight:bold;">^→</span> (arrow)   go back/forward one word
        <span style="font-weight:bold;">^H</span>  <span style="font-weight:bold;">^D</span>           delete previous/current character
        <span style="font-weight:bold;">^T</span>               transpose previous and current characters
        <span style="font-weight:bold;">^U</span>  <span style="font-weight:bold;">^K</span>           clear from cursor to beginning/end of line
        <span style="font-weight:bold;">^Y</span>               paste from cell clipboard
        <span style="font-weight:bold;">Backspace</span>  <span style="font-weight:bold;">Del</span>   delete previous/current character
        <span style="font-weight:bold;">Insert</span>           toggle insert mode
        <span style="font-weight:bold;">Up</span>  <span style="font-weight:bold;">Down</span>         set contents to previous/next in history
        <span style="font-weight:bold;">Tab</span>  <span style="font-weight:bold;">Shift+Tab</span>   autocomplete input (when available)
        <span style="font-weight:bold;">Shift+Arrow</span>      move cursor in direction of <span style="font-weight:bold;">Arrow</span> and re-enter edit mode

   <span style="font-weight:bold;">Data</span> <span style="font-weight:bold;">Toolkit</span>
      <span style="font-weight:bold;">o</span> <span style="text-decoration:underline;">input</span>         open <span style="text-decoration:underline;">input</span> in <span style="font-weight:bold;">VisiData</span>
     <span style="font-weight:bold;">^S</span> <span style="font-weight:bold;">g^S</span> <span style="text-decoration:underline;">filename</span>  save current/all sheet(s) to <span style="text-decoration:underline;">filename</span> in format determined by extension (default .tsv)
                      Note: if the format does not support multisave, or the <span style="text-decoration:underline;">filename</span> ends in a <span style="font-weight:bold;">/</span>, a directory will be created.
     <span style="font-weight:bold;">z^S</span> <span style="text-decoration:underline;">filename</span>     save current column only to <span style="text-decoration:underline;">filename</span> in format determined by extension (default .tsv)
     <span style="font-weight:bold;">^D</span> <span style="text-decoration:underline;">filename.vd</span>   save <span style="font-weight:bold;">CommandLog</span> to <span style="text-decoration:underline;">filename.vd</span> file
     <span style="font-weight:bold;">A</span>                open new blank sheet with one column
     <span style="font-weight:bold;">T</span>                open new sheet that has rows and columns of current sheet transposed

      <span style="font-weight:bold;">+</span> <span style="text-decoration:underline;">aggregator</span>    add <span style="text-decoration:underline;">aggregator</span> to current column (see <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span>)
     <span style="font-weight:bold;">z+</span> <span style="text-decoration:underline;">aggregator</span>    display result of <span style="text-decoration:underline;">aggregator</span> over values in selected rows for current column; store result in <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span>
      <span style="font-weight:bold;">&amp;</span>               concatenate top two sheets in <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Stack</span>
     <span style="font-weight:bold;">g&amp;</span>               concatenate all sheets in <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Stack</span>

   <span style="font-weight:bold;">Data</span> <span style="font-weight:bold;">Visualization</span>
      <span style="font-weight:bold;">.</span> (dot)       plot current numeric column vs key columns. The numeric key column is used for the x-axis; categorical key column values determine color.
     <span style="font-weight:bold;">g.</span>             plot a graph of all visible numeric columns vs key columns.

     If rows on the current sheet represent plottable coordinates (as in .shp or vector .mbtiles sources),  <span style="font-weight:bold;">.</span> plots the current row, and <span style="font-weight:bold;">g.</span> plots all selected rows (or all rows if none selected).

     <span style="font-weight:bold;">Canvas-specific</span> <span style="font-weight:bold;">Commands</span>
         <span style="font-weight:bold;">+</span>   <span style="font-weight:bold;">-</span>              increase/decrease zoom level, centered on cursor
         <span style="text-decoration:underline;">_</span> (underscore)     zoom to fit full extent
        <span style="font-weight:bold;">z</span><span style="text-decoration:underline;">_</span> (underscore)     set aspect ratio
         <span style="font-weight:bold;">x</span> <span style="text-decoration:underline;">xmin</span> <span style="text-decoration:underline;">xmax</span>        set <span style="text-decoration:underline;">xmin</span>/<span style="text-decoration:underline;">xmax</span> on graph
         <span style="font-weight:bold;">y</span> <span style="text-decoration:underline;">ymin</span> <span style="text-decoration:underline;">ymax</span>        set <span style="text-decoration:underline;">ymin</span>/<span style="text-decoration:underline;">ymax</span> on graph
         <span style="font-weight:bold;">s</span>   <span style="font-weight:bold;">t</span>   <span style="font-weight:bold;">u</span>          select/toggle/unselect rows on source sheet contained within canvas cursor
        <span style="font-weight:bold;">gs</span>  <span style="font-weight:bold;">gt</span>  <span style="font-weight:bold;">gu</span>          select/toggle/unselect rows on source sheet visible on screen
         <span style="font-weight:bold;">d</span>                  delete rows on source sheet contained within canvas cursor
        <span style="font-weight:bold;">gd</span>                  delete rows on source sheet visible on screen
         <span style="font-weight:bold;">Enter</span>              open sheet of source rows contained within canvas cursor
        <span style="font-weight:bold;">gEnter</span>              open sheet of source rows visible on screen
         <span style="font-weight:bold;">1</span> - <span style="font-weight:bold;">9</span>              toggle display of layers
        <span style="font-weight:bold;">^L</span>                  redraw all pixels on canvas
         <span style="font-weight:bold;">v</span>                  toggle <span style="font-weight:bold;">show</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">graph</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">labels</span> option
        <span style="font-weight:bold;">mouse</span> <span style="font-weight:bold;">scrollwheel</span>   zoom in/out of canvas
        <span style="font-weight:bold;">left</span> <span style="font-weight:bold;">click-drag</span>     set canvas cursor
        <span style="font-weight:bold;">right</span> <span style="font-weight:bold;">click-drag</span>    scroll canvas

   <span style="font-weight:bold;">Split</span> <span style="font-weight:bold;">Screen</span>
      <span style="font-weight:bold;">Z</span>             split screen in half, so that second sheet on the stack is visible in a second pane
     <span style="font-weight:bold;">zZ</span>             split screen, and queries for height of second pane

     <span style="font-weight:bold;">Split</span> <span style="font-weight:bold;">Window</span> <span style="font-weight:bold;">specific</span> <span style="font-weight:bold;">Commands</span>
        <span style="font-weight:bold;">gZ</span>                  close an already split screen, current pane full screens
         <span style="font-weight:bold;">Z</span>                  push second sheet on current pane's stack to the top of the other pane's stack
         <span style="font-weight:bold;">Tab</span>                jump to other pane
        <span style="font-weight:bold;">gTab</span>                swap panes
        <span style="font-weight:bold;">g^^</span> (g Ctrl+^)      cycle through sheets

   <span style="font-weight:bold;">Other</span> <span style="font-weight:bold;">Commands</span>
     <span style="font-weight:bold;">Q</span>                quit current sheet and remove it from the <span style="font-weight:bold;">CommandLog</span>
     <span style="font-weight:bold;">v</span>                toggle sheet-specific visibility (multi-line rows on Sheet, legends/axes on Graph)

      <span style="font-weight:bold;">^E</span>  <span style="font-weight:bold;">g^E</span>         view traceback for most recent error(s)
     <span style="font-weight:bold;">z^E</span>              view traceback for error in current cell

      <span style="font-weight:bold;">^L</span>              refresh screen
      <span style="font-weight:bold;">^R</span>              reload current sheet
     <span style="font-weight:bold;">z^R</span>              clear cache for current column
      <span style="font-weight:bold;">^Z</span>              suspend VisiData process
      <span style="font-weight:bold;">^G</span>              show cursor position and bounds of current sheet on status line
      <span style="font-weight:bold;">^V</span>              show version and copyright information on status line
      <span style="font-weight:bold;">^P</span>              open <span style="font-weight:bold;">Status</span> <span style="font-weight:bold;">History</span>
     m <span style="text-decoration:underline;">keystroke</span>      first, begin recording macro; second, prompt for <span style="text-decoration:underline;">keystroke</span> <span style="text-decoration:underline;">No,</span> <span style="text-decoration:underline;">and</span> <span style="text-decoration:underline;">complete</span> <span style="text-decoration:underline;">recording.</span> <span style="text-decoration:underline;">Macro</span> <span style="text-decoration:underline;">can</span> <span style="text-decoration:underline;">then</span> <span style="text-decoration:underline;">be</span> <span style="text-decoration:underline;">executed</span> <span style="text-decoration:underline;">everytime</span> <span style="text-decoration:underline;">provided</span> <span style="text-decoration:underline;">keystroke</span> <span style="text-decoration:underline;">is</span> <span style="text-decoration:underline;">used.</span> <span style="text-decoration:underline;">Will</span> <span style="text-decoration:underline;">override</span> <span style="text-decoration:underline;">existing</span> <span style="text-decoration:underline;">keybinding.</span> <span style="text-decoration:underline;">Macros</span> <span style="text-decoration:underline;">will</span> <span style="text-decoration:underline;">run</span> <span style="text-decoration:underline;">on</span> <span style="text-decoration:underline;">current</span> <span style="text-decoration:underline;">row,</span> <span style="text-decoration:underline;">column,</span> <span style="text-decoration:underline;">sheet.</span>
     gm               open an index of all existing macros. Can be directly viewed with <span style="font-weight:bold;">Enter</span>, and then modified with <span style="font-weight:bold;">^S</span>.

      <span style="font-weight:bold;">^Y</span>  <span style="font-weight:bold;">z^Y</span>  <span style="font-weight:bold;">g^Y</span>    open current row/cell/sheet as Python object
      <span style="font-weight:bold;">^X</span> <span style="text-decoration:underline;">expr</span>         evaluate Python <span style="text-decoration:underline;">expr</span> and opens result as Python object
     <span style="font-weight:bold;">z^X</span> <span style="text-decoration:underline;">expr</span>         evaluate Python <span style="text-decoration:underline;">expr</span>, in context of current row, and open result as Python object
     <span style="font-weight:bold;">g^X</span> <span style="text-decoration:underline;">stmt</span>         execute Python <span style="text-decoration:underline;">stmt</span> in the global scope

   <span style="font-weight:bold;">Internal</span> <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">List</span>
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">VisiDataMenu</span> (Shift+V)      browse list of core sheets
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Directory</span> <span style="font-weight:bold;">Sheet</span>             browse properties of files in a directory
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Plugins</span> <span style="font-weight:bold;">Sheet</span>               browse, install, and (de)activate plugins
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span> (Alt+Shift+M)        browse saved values, including clipboard

     <span style="font-weight:bold;">Metasheets</span>
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Columns</span> <span style="font-weight:bold;">Sheet</span> (Shift+C)     edit column properties
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Sheet</span> (Shift+S)      jump between sheets or join them together
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Options</span> <span style="font-weight:bold;">Sheet</span> (Shift+O)     edit configuration options
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Commandlog</span> (Shift+D)        modify and save commands for replay
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Error</span> <span style="font-weight:bold;">Sheet</span> (Ctrl+E)            view last error
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Status</span> <span style="font-weight:bold;">History</span> (Ctrl+P)         view history of status messages
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Threads</span> <span style="font-weight:bold;">Sheet</span> (Ctrl+T)          view, cancel, and profile asynchronous threads

     <span style="font-weight:bold;">Derived</span> <span style="font-weight:bold;">Sheets</span>
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span> (Shift+F)   group rows by column value, with aggregations of other columns
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Describe</span> <span style="font-weight:bold;">Sheet</span> (Shift+I)    view summary statistics for each column
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Pivot</span> <span style="font-weight:bold;">Table</span> (Shift+W)       group rows by key and summarize current column
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Melted</span> <span style="font-weight:bold;">Sheet</span> (Shift+M)      unpivot non-key columns into variable/value columns
      <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">Transposed</span> <span style="font-weight:bold;">Sheet</span> (Shift+T)   open new sheet with rows and columns transposed

   <span style="font-weight:bold;">INTERNAL</span> <span style="font-weight:bold;">SHEETS</span>
   <span style="font-weight:bold;">VisiDataMenu</span> <span style="font-weight:bold;">(Shift+V)</span>
     (sheet-specific commands)
        <span style="font-weight:bold;">Enter</span>            load sheet in current row

   <span style="font-weight:bold;">Directory</span> <span style="font-weight:bold;">Sheet</span>
     (global commands)
        <span style="font-weight:bold;">Space</span> <span style="text-decoration:underline;">open-dir-current</span>
                         open the <span style="font-weight:bold;">Directory</span> <span style="font-weight:bold;">Sheet</span> for the current directory
     (sheet-specific commands)
        <span style="font-weight:bold;">Enter</span>  <span style="font-weight:bold;">gEnter</span>    open current/selected file(s) as new sheet(s)
         <span style="font-weight:bold;">^O</span>  <span style="font-weight:bold;">g^O</span>         open current/selected file(s) in external $EDITOR
         <span style="font-weight:bold;">^R</span>  <span style="font-weight:bold;">z^R</span>  <span style="font-weight:bold;">gz^R</span>   reload information for all/current/selected file(s)

   <span style="font-weight:bold;">Plugins</span> <span style="font-weight:bold;">Sheet</span>
     Browse through a list of available plugins. VisiData needs to be restarted before plugin activation takes effect. Installation may require internet access.
     (global commands)
        <span style="font-weight:bold;">Space</span> <span style="text-decoration:underline;">open-plugins</span>
                         open the <span style="font-weight:bold;">Plugins</span> <span style="font-weight:bold;">Sheet</span>
     (sheet-specific commands)
        <span style="font-weight:bold;">a</span>                install and activate current plugin
        <span style="font-weight:bold;">d</span>                deactivate current plugin

   <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span>
     Browse through a list of stored values, referanceable in expressions through their <span style="font-weight:bold;">name</span>.
     (global commands)
        <span style="font-weight:bold;">Alt+Shift+M</span>      open the <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span>
        <span style="font-weight:bold;">Alt+M</span> <span style="text-decoration:underline;">name</span>       store value in current cell in <span style="font-weight:bold;">Memory</span> <span style="font-weight:bold;">Sheet</span> under <span style="text-decoration:underline;">name</span>
     (sheet-specific commands)
        <span style="font-weight:bold;">e</span>                edit either value or name, to edit reference

   <span style="font-weight:bold;">METASHEETS</span>
   <span style="font-weight:bold;">Columns</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(Shift+C)</span>
     Properties of columns on the source sheet can be changed with standard editing commands (<span style="font-weight:bold;">e</span> <span style="font-weight:bold;">ge</span> <span style="font-weight:bold;">g=</span> <span style="font-weight:bold;">Del</span>) on the <span style="font-weight:bold;">Columns</span> <span style="font-weight:bold;">Sheet</span>. Multiple aggregators can be set by listing them (separated by spaces) in the aggregators column. The 'g' commands affect the selected rows, which are the literal columns on the source sheet.
     (global commands)
        <span style="font-weight:bold;">gC</span>               open <span style="font-weight:bold;">Columns</span> <span style="font-weight:bold;">Sheet</span> with all visible columns from all sheets
     (sheet-specific commands)
         <span style="font-weight:bold;">&amp;</span>               add column from concatenating selected source columns
        <span style="font-weight:bold;">g!</span> <span style="font-weight:bold;">gz!</span>           toggle/unset selected columns as key columns on source sheet
        <span style="font-weight:bold;">g+</span> <span style="text-decoration:underline;">aggregator</span>    add Ar aggregator No to selected source columns
        <span style="font-weight:bold;">g-</span> (hyphen)      hide selected columns on source sheet
        <span style="font-weight:bold;">g~</span> <span style="font-weight:bold;">g#</span> <span style="font-weight:bold;">g%</span> <span style="font-weight:bold;">g$</span> <span style="font-weight:bold;">g@</span> <span style="font-weight:bold;">gz#</span> <span style="font-weight:bold;">z%</span>
                         set type of selected columns on source sheet to str/int/float/currency/date/len/floatsi
         <span style="font-weight:bold;">Enter</span>           open a <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span> sheet grouped by column referenced in current row

   <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(Shift+S)</span>
     open <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Stack</span>, which contains only the active sheets on the current stack
     (global commands)
        <span style="font-weight:bold;">gS</span>               open <span style="font-weight:bold;">Sheets</span> <span style="font-weight:bold;">Sheet</span>, which contains all sheets from current session, active and inactive
        <span style="font-weight:bold;">Alt</span> <span style="text-decoration:underline;">number</span>       jump to sheet <span style="text-decoration:underline;">number</span>
     (sheet-specific commands)
         <span style="font-weight:bold;">Enter</span>           jump to sheet referenced in current row
        <span style="font-weight:bold;">gEnter</span>           push selected sheets to top of sheet stack
         <span style="font-weight:bold;">a</span>               add row to reference a new blank sheet
        <span style="font-weight:bold;">gC</span>  <span style="font-weight:bold;">gI</span>           open <span style="font-weight:bold;">Columns</span> <span style="font-weight:bold;">Sheet</span>/<span style="font-weight:bold;">Describe</span> <span style="font-weight:bold;">Sheet</span> with all visible columns from selected sheets
        <span style="font-weight:bold;">g^R</span>              reload all selected sheets
        <span style="font-weight:bold;">z^C</span>  <span style="font-weight:bold;">gz^C</span>        abort async threads for current/selected sheets(s)
        <span style="font-weight:bold;">g^S</span>              save selected or all sheets
         <span style="font-weight:bold;">&amp;</span> <span style="text-decoration:underline;">jointype</span>      merge selected sheets with visible columns from all, keeping rows according to <span style="text-decoration:underline;">jointype</span>:
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">inner</span>  keep only rows which match keys on all sheets
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">outer</span>  keep all rows from first selected sheet
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">full</span>   keep all rows from all sheets (union)
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">diff</span>   keep only rows NOT in all sheets
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">append</span> keep all rows from all sheets (concatenation)
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">extend</span> copy first selected sheet, keeping all rows and sheet type, and extend with columns from other sheets
                         <span style="font-weight:bold;">.</span>  <span style="font-weight:bold;">merge</span>  mostly keep all rows from first selected sheet, except prioritise cells with non-null/non-error values

   <span style="font-weight:bold;">Options</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(Shift+O)</span>
     (global commands)
        <span style="font-weight:bold;">Shift+O</span>          edit global options (apply to <span style="font-weight:bold;">all</span> <span style="font-weight:bold;">sheets</span>)
        <span style="font-weight:bold;">zO</span>               edit sheet options (apply to <span style="font-weight:bold;">current</span> <span style="font-weight:bold;">sheet</span> only)
        <span style="font-weight:bold;">gO</span>               open <span style="font-weight:bold;">options.config</span> as <span style="font-weight:bold;">TextSheet</span>
     (sheet-specific commands)
        <span style="font-weight:bold;">Enter</span>  <span style="font-weight:bold;">e</span>         edit option at current row
        <span style="font-weight:bold;">d</span>                remove option override for this context

   <span style="font-weight:bold;">CommandLog</span> <span style="font-weight:bold;">(Shift+D)</span>
     (global commands)
        <span style="font-weight:bold;">D</span>                open current sheet's <span style="font-weight:bold;">CommandLog</span> with all other loose ends removed; includes commands from parent sheets
        <span style="font-weight:bold;">gD</span>               open global <span style="font-weight:bold;">CommandLog</span> for all commands executed in the current session
        <span style="font-weight:bold;">zD</span>               open current sheet's <span style="font-weight:bold;">CommandLog</span> with the parent sheets commands' removed
     (sheet-specific commands)
          <span style="font-weight:bold;">x</span>              replay command in current row
         <span style="font-weight:bold;">gx</span>              replay contents of entire CommandLog
         <span style="font-weight:bold;">^C</span>              abort replay

   <span style="font-weight:bold;">DERIVED</span> <span style="font-weight:bold;">SHEETS</span>
   <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span> <span style="font-weight:bold;">(Shift+F)</span>
     A <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span> groups rows by one or more columns, and includes summary columns for those with aggregators.
     (global commands)
        <span style="font-weight:bold;">gF</span>               open Frequency Table, grouped by all key columns on source sheet
        <span style="font-weight:bold;">zF</span>               open one-line summary for all rows and selected rows
     (sheet-specific commands)
         <span style="font-weight:bold;">s</span>   <span style="font-weight:bold;">t</span>   <span style="font-weight:bold;">u</span>       select/toggle/unselect these entries in source sheet
         <span style="font-weight:bold;">Enter</span>  <span style="font-weight:bold;">gEnter</span>   open copy of source sheet with rows that are grouped in current cell / selected rows

   <span style="font-weight:bold;">Describe</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(Shift+I)</span>
     A <span style="font-weight:bold;">Describe</span> <span style="font-weight:bold;">Sheet</span> contains descriptive statistics for all visible columns.
     (global commands)
        <span style="font-weight:bold;">gI</span>               open <span style="font-weight:bold;">Describe</span> <span style="font-weight:bold;">Sheet</span> for all visible columns on all sheets
     (sheet-specific commands)
        <span style="font-weight:bold;">zs</span>  <span style="font-weight:bold;">zu</span>           select/unselect rows on source sheet that are being described in current cell
         <span style="font-weight:bold;">!</span>               toggle/unset current column as a key column on source sheet
         <span style="font-weight:bold;">Enter</span>           open a <span style="font-weight:bold;">Frequency</span> <span style="font-weight:bold;">Table</span> sheet grouped on column referenced in current row
        <span style="font-weight:bold;">zEnter</span>           open copy of source sheet with rows described in current cell

   <span style="font-weight:bold;">Pivot</span> <span style="font-weight:bold;">Table</span> <span style="font-weight:bold;">(Shift+W)</span>
     Set key column(s) and aggregators on column(s) before pressing <span style="font-weight:bold;">Shift+W</span> on the column to pivot.
     (sheet-specific commands)
         <span style="font-weight:bold;">Enter</span>           open sheet of source rows aggregated in current pivot row
        <span style="font-weight:bold;">zEnter</span>           open sheet of source rows aggregated in current pivot cell

   <span style="font-weight:bold;">Melted</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(Shift+M)</span>
     Open Melted Sheet (unpivot), with key columns retained and all non-key columns reduced to Variable-Value rows.
     (global commands)
        <span style="font-weight:bold;">gM</span> <span style="text-decoration:underline;">regex</span>         open Melted Sheet (unpivot), with key columns retained and <span style="text-decoration:underline;">regex</span> capture groups determining how the non-key columns will be reduced to Variable-Value rows.

   <span style="font-weight:bold;">Python</span> <span style="font-weight:bold;">Object</span> <span style="font-weight:bold;">Sheet</span> <span style="font-weight:bold;">(^X</span> <span style="font-weight:bold;">^Y</span> <span style="font-weight:bold;">g^Y</span> <span style="font-weight:bold;">z^Y)</span>
     (sheet-specific commands)
         <span style="font-weight:bold;">Enter</span>           dive further into Python object
         <span style="font-weight:bold;">v</span>               toggle show/hide for methods and hidden properties
        <span style="font-weight:bold;">gv</span>  <span style="font-weight:bold;">zv</span>           show/hide methods and hidden properties

<span style="font-weight:bold;">COMMANDLINE</span> <span style="font-weight:bold;">OPTIONS</span>
     Add <span style="font-weight:bold;">-n</span>/<span style="font-weight:bold;">--nonglobal</span> to make subsequent CLI options sheet-specific (applying only to paths specified directly on the CLI). By default, CLI options apply to all sheets.

     Options can also be set via the <span style="text-decoration:underline;">Options</span> <span style="text-decoration:underline;">Sheet</span> or a <span style="text-decoration:underline;">.visidatarc</span> (see <span style="text-decoration:underline;">FILES</span>).

     <span style="font-weight:bold;">-P</span>=<span style="text-decoration:underline;">longname</span>                  preplay <span style="text-decoration:underline;">longname</span> before replay or regular launch; limited to <span style="font-weight:bold;">Base</span> <span style="font-weight:bold;">Sheet</span> bound commands
     <span style="font-weight:bold;">+</span><span style="text-decoration:underline;">toplevel</span>:<span style="text-decoration:underline;">subsheet</span>:<span style="text-decoration:underline;">col</span>:<span style="text-decoration:underline;">row</span>   launch vd with <span style="text-decoration:underline;">subsheet</span> of <span style="text-decoration:underline;">toplevel</span> at top-of-stack, and cursor at <span style="text-decoration:underline;">col</span> and <span style="text-decoration:underline;">row</span>; all arguments are optional

     <span style="font-weight:bold;">-f</span>, <span style="font-weight:bold;">--filetype</span>=<span style="text-decoration:underline;">filetype</span>      tsv                set loader to use for <span style="text-decoration:underline;">filetype</span> instead of file extension
     <span style="font-weight:bold;">-y</span>, <span style="font-weight:bold;">--confirm-overwrite</span>=<span style="text-decoration:underline;">F</span>    True               overwrite existing files without confirmation
     <span style="font-weight:bold;">--mouse-interval</span>=<span style="text-decoration:underline;">int</span>         1                  max time between press/release for click (ms)
     <span style="font-weight:bold;">--null-value</span>=<span style="text-decoration:underline;">NoneType</span>        None               a value to be counted as null
     <span style="font-weight:bold;">--undo</span>=<span style="text-decoration:underline;">bool</span>                  True               enable undo/redo
     <span style="font-weight:bold;">--col-cache-size</span>=<span style="text-decoration:underline;">int</span>         0                  max number of cache entries in each cached column
     <span style="font-weight:bold;">--clean-names</span>                False              clean column/sheet names to be valid Python identifiers
     <span style="font-weight:bold;">--default-width</span>=<span style="text-decoration:underline;">int</span>          20                 default column width
     <span style="font-weight:bold;">--default-height</span>=<span style="text-decoration:underline;">int</span>         10                 default column height
     <span style="font-weight:bold;">--textwrap-cells</span>=<span style="text-decoration:underline;">bool</span>        True               wordwrap text for multiline rows
     <span style="font-weight:bold;">--quitguard</span>                  False              confirm before quitting last sheet
     <span style="font-weight:bold;">--debug</span>                      False              exit on error and display stacktrace
     <span style="font-weight:bold;">--skip</span>=<span style="text-decoration:underline;">int</span>                   0                  skip N rows before header
     <span style="font-weight:bold;">--header</span>=<span style="text-decoration:underline;">int</span>                 1                  parse first N rows as column names
     <span style="font-weight:bold;">--load-lazy</span>                  False              load subsheets always (False) or lazily (True)
     <span style="font-weight:bold;">--force-256-colors</span>           False              use 256 colors even if curses reports fewer
     <span style="font-weight:bold;">--note-pending</span>=<span style="text-decoration:underline;">str</span>           ⌛                 note to display for pending cells
     <span style="font-weight:bold;">--note-format-exc</span>=<span style="text-decoration:underline;">str</span>        ?                  cell note for an exception during formatting
     <span style="font-weight:bold;">--note-getter-exc</span>=<span style="text-decoration:underline;">str</span>        !                  cell note for an exception during computation
     <span style="font-weight:bold;">--note-type-exc</span>=<span style="text-decoration:underline;">str</span>          !                  cell note for an exception during type conversion
     <span style="font-weight:bold;">--scroll-incr</span>=<span style="text-decoration:underline;">int</span>            3                  amount to scroll with scrollwheel
     <span style="font-weight:bold;">--name-joiner</span>=<span style="text-decoration:underline;">str</span>            _                  string to join sheet or column names
     <span style="font-weight:bold;">--value-joiner</span>=<span style="text-decoration:underline;">str</span>                              string to join display values
     <span style="font-weight:bold;">--wrap</span>                       False              wrap text to fit window width on TextSheet
     <span style="font-weight:bold;">--save-filetype</span>=<span style="text-decoration:underline;">str</span>          tsv                specify default file type to save as
     <span style="font-weight:bold;">--profile</span>=<span style="text-decoration:underline;">str</span>                                   filename to save binary profiling data
     <span style="font-weight:bold;">--min-memory-mb</span>=<span style="text-decoration:underline;">int</span>          0                  minimum memory to continue loading and async processing
     <span style="font-weight:bold;">--input-history</span>=<span style="text-decoration:underline;">str</span>                             basename of file to store persistent input history
     <span style="font-weight:bold;">--encoding</span>=<span style="text-decoration:underline;">str</span>               utf-8              encoding passed to codecs.open
     <span style="font-weight:bold;">--encoding-errors</span>=<span style="text-decoration:underline;">str</span>        surrogateescape    encoding_errors passed to codecs.open
     <span style="font-weight:bold;">--bulk-select-clear</span>          False              clear selected rows before new bulk selections
     <span style="font-weight:bold;">--some-selected-rows</span>         False              if no rows selected, if True, someSelectedRows returns all rows; if False, fails
     <span style="font-weight:bold;">--delimiter</span>=<span style="text-decoration:underline;">str</span>                                 field delimiter to use for tsv/usv filetype
     <span style="font-weight:bold;">--row-delimiter</span>=<span style="text-decoration:underline;">str</span>                             &quot; row delimiter to use for tsv/usv filetype
     <span style="font-weight:bold;">--tsv-safe-newline</span>=<span style="text-decoration:underline;">str</span>                          replacement for newline character when saving to tsv
     <span style="font-weight:bold;">--tsv-safe-tab</span>=<span style="text-decoration:underline;">str</span>                              replacement for tab character when saving to tsv
     <span style="font-weight:bold;">--visibility</span>=<span style="text-decoration:underline;">int</span>             0                  visibility level (0=low, 1=high)
     <span style="font-weight:bold;">--expand-col-scanrows</span>=<span style="text-decoration:underline;">int</span>    1000               number of rows to check when expanding columns (0 = all)
     <span style="font-weight:bold;">--json-indent</span>=<span style="text-decoration:underline;">NoneType</span>       None               indent to use when saving json
     <span style="font-weight:bold;">--json-sort-keys</span>             False              sort object keys when saving to json
     <span style="font-weight:bold;">--default-colname</span>=<span style="text-decoration:underline;">str</span>                           column name to use for non-dict rows
     <span style="font-weight:bold;">--filetype</span>=<span style="text-decoration:underline;">str</span>                                  specify file type
     <span style="font-weight:bold;">--confirm-overwrite</span>=<span style="text-decoration:underline;">bool</span>     True               whether to prompt for overwrite confirmation on save
     <span style="font-weight:bold;">--safe-error</span>=<span style="text-decoration:underline;">str</span>             #ERR               error string to use while saving
     <span style="font-weight:bold;">--clipboard-copy-cmd</span>=<span style="text-decoration:underline;">str</span>                        command to copy stdin to system clipboard
     <span style="font-weight:bold;">--clipboard-paste-cmd</span>=<span style="text-decoration:underline;">str</span>                       command to get contents of system clipboard
     <span style="font-weight:bold;">--fancy-chooser</span>              False              a nicer selection interface for aggregators and jointype
     <span style="font-weight:bold;">--describe-aggrs</span>=<span style="text-decoration:underline;">str</span>         mean stdev         numeric aggregators to calculate on Describe sheet
     <span style="font-weight:bold;">--histogram-bins</span>=<span style="text-decoration:underline;">int</span>         0                  number of bins for histogram of numeric columns
     <span style="font-weight:bold;">--numeric-binning</span>            False              bin numeric columns into ranges
     <span style="font-weight:bold;">--replay-wait</span>=<span style="text-decoration:underline;">float</span>          0.0                time to wait between replayed commands, in seconds
     <span style="font-weight:bold;">--replay-movement</span>            False              insert movements during replay
     <span style="font-weight:bold;">--visidata-dir</span>=<span style="text-decoration:underline;">str</span>           ~/.visidata/       directory to load and store additional files
     <span style="font-weight:bold;">--rowkey-prefix</span>=<span style="text-decoration:underline;">str</span>          キ                 string prefix for rowkey in the cmdlog
     <span style="font-weight:bold;">--cmdlog-histfile</span>=<span style="text-decoration:underline;">str</span>                           file to autorecord each cmdlog action to
     <span style="font-weight:bold;">--regex-flags</span>=<span style="text-decoration:underline;">str</span>            I                  flags to pass to re.compile() [AILMSUX]
     <span style="font-weight:bold;">--regex-maxsplit</span>=<span style="text-decoration:underline;">int</span>         0                  maxsplit to pass to regex.split
     <span style="font-weight:bold;">--default-sample-size</span>=<span style="text-decoration:underline;">int</span>    100                number of rows to sample for regex.split
     <span style="font-weight:bold;">--show-graph-labels</span>=<span style="text-decoration:underline;">bool</span>     True               show axes and legend on graph
     <span style="font-weight:bold;">--plot-colors</span>=<span style="text-decoration:underline;">str</span>                               list of distinct colors to use for plotting distinct objects
     <span style="font-weight:bold;">--zoom-incr</span>=<span style="text-decoration:underline;">float</span>            2.0                amount to multiply current zoomlevel when zooming
     <span style="font-weight:bold;">--motd-url</span>=<span style="text-decoration:underline;">str</span>                                  source of randomized startup messages
     <span style="font-weight:bold;">--dir-recurse</span>                False              walk source path recursively on DirSheet
     <span style="font-weight:bold;">--dir-hidden</span>                 False              load hidden files on DirSheet
     <span style="font-weight:bold;">--config</span>=<span style="text-decoration:underline;">str</span>                 ~/.visidatarc      config file to exec in Python
     <span style="font-weight:bold;">--play</span>=<span style="text-decoration:underline;">str</span>                                      file.vd to replay
     <span style="font-weight:bold;">--batch</span>                      False              replay in batch mode (with no interface and all status sent to stdout)
     <span style="font-weight:bold;">--output</span>=<span style="text-decoration:underline;">NoneType</span>            None               save the final visible sheet to output at the end of replay
     <span style="font-weight:bold;">--preplay</span>=<span style="text-decoration:underline;">str</span>                                   longnames to preplay before replay
     <span style="font-weight:bold;">--imports</span>=<span style="text-decoration:underline;">str</span>                plugins            imports to preload before .visidatarc (command-line only)
     <span style="font-weight:bold;">--incr-base</span>=<span style="text-decoration:underline;">float</span>            1.0                start value for column increments
     <span style="font-weight:bold;">--csv-dialect</span>=<span style="text-decoration:underline;">str</span>            excel              dialect passed to csv.reader
     <span style="font-weight:bold;">--csv-delimiter</span>=<span style="text-decoration:underline;">str</span>          ,                  delimiter passed to csv.reader
     <span style="font-weight:bold;">--csv-quotechar</span>=<span style="text-decoration:underline;">str</span>          &quot;                  quotechar passed to csv.reader
     <span style="font-weight:bold;">--csv-skipinitialspace</span>=<span style="text-decoration:underline;">bool</span>  True               skipinitialspace passed to csv.reader
     <span style="font-weight:bold;">--csv-escapechar</span>=<span style="text-decoration:underline;">NoneType</span>    None               escapechar passed to csv.reader
     <span style="font-weight:bold;">--csv-lineterminator</span>=<span style="text-decoration:underline;">str</span>                        &quot; lineterminator passed to csv.writer
     <span style="font-weight:bold;">--safety-first</span>               False              sanitize input/output to handle edge cases, with a performance cost
     <span style="font-weight:bold;">--fixed-rows</span>=<span style="text-decoration:underline;">int</span>             1000               number of rows to check for fixed width columns
     <span style="font-weight:bold;">--fixed-maxcols</span>=<span style="text-decoration:underline;">int</span>          0                  max number of fixed-width columns to create (0 is no max)
     <span style="font-weight:bold;">--postgres-schema</span>=<span style="text-decoration:underline;">str</span>        public             The desired schema for the Postgres database
     <span style="font-weight:bold;">--http-max-next</span>=<span style="text-decoration:underline;">int</span>          0                  max next.url pages to follow in http response
     <span style="font-weight:bold;">--html-title</span>=<span style="text-decoration:underline;">str</span>             &lt;h2&gt;{sheet.name}&lt;/h2&gt;
                                                     table header when saving to html
     <span style="font-weight:bold;">--pcap-internet</span>=<span style="text-decoration:underline;">str</span>          n                  (y/s/n) if save_dot includes all internet hosts separately (y), combined (s), or does not include the internet (n)
     <span style="font-weight:bold;">--graphviz-edge-labels</span>=<span style="text-decoration:underline;">bool</span>  True               whether to include edge labels on graphviz diagrams
     <span style="font-weight:bold;">--pdf-tables</span>                 False              parse PDF for tables instead of pages of text
     <span style="font-weight:bold;">--plugins-url</span>=<span style="text-decoration:underline;">str</span>            https://visidata.org/plugins/plugins.jsonl
                                                     source of plugins sheet

   <span style="font-weight:bold;">DISPLAY</span> <span style="font-weight:bold;">OPTIONS</span>
     Display options can only be set via the <span style="text-decoration:underline;">Options</span> <span style="text-decoration:underline;">Sheet</span> or a <span style="text-decoration:underline;">.visidatarc</span> (see <span style="text-decoration:underline;">FILES</span>).

     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">splitwin</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pct</span>   0                   height of second sheet on screen
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">currency</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>   %.02f               default fmtstr to format for currency values
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">float</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>      {:.02f}             default fmtstr to format for float values
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">int</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>        {:.0f}              default fmtstr to format for int values
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">date</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>       %Y-%m-%d            default fmtstr to strftime for date values
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">note</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">none</span>      ⌀                   visible contents of a cell whose value is None
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">truncator</span>      …                   indicator that the contents are only partially visible
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">oddspace</span>       ·                   displayable character for odd whitespace
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">more</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">left</span>      &lt;                   header note indicating more columns to the left
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">more</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">right</span>     &gt;                   header note indicating more columns to the right
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">error</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">val</span>                          displayed contents for computation exception
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">ambig</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">width</span>    1                   width to use for unicode chars marked ambiguous
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pending</span>                            string to display in pending cells
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">note</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pending</span>  bold magenta        color of note in pending cells
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">note</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">type</span>     226 yellow          color of cell note for non-str types in anytype columns
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">note</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">row</span>      220 yellow          color of row note on left edge
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">column</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     |                   separator between columns
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">keycol</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║                   separator between key columns and rest of columns
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">rowtop</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     |
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">rowmid</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ⁝
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">rowbot</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ⁝
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">rowend</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">keytop</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">keymid</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">keybot</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">endtop</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">endmid</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">endbot</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>     ║
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">selected</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">note</span>  •
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sort</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">asc</span>       ↑↟⇞⇡⇧⇑              characters for ascending sort
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sort</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">desc</span>      ↓↡⇟⇣⇩⇓              characters for descending sort
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">default</span>       white on black      the default fg and bg colors
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">default</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">hdr</span>   bold                color of the column headers
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">bottom</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">hdr</span>    underline           color of the bottom header row
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">current</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">row</span>   reverse             color of the cursor row
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">current</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">col</span>   bold                color of the cursor column
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">current</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">hdr</span>   bold reverse        color of the header for the cursor column
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">column</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>    246 blue            color of column separators
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">key</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">col</span>       81 cyan             color of key columns
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">hidden</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">col</span>    8                   color of hidden columns on metasheets
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">selected</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">row</span>  215 yellow          color of selected rows
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">rstatus</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>     {sheet.longname} {sheet.nRows:9d} {sheet.rowtype} {sheet.options.disp_selected_note}{sheet.nSelectedRows}
                                             right-side status format string
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fmt</span>     {sheet.shortcut}› {sheet.name}|
                                             status line prefix
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">lstatus</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">max</span>    0                   maximum length of left status line
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">sep</span>      |                  separator between statuses
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">keystrokes</span>    white               color of input keystrokes on status line
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span>        bold                status line color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">error</span>         red                 error message color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">warning</span>       yellow              warning message color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">top</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span>    underline           top window status bar color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">active</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span> bold                 active window status bar color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">inactive</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span> 8                 inactive window status bar color
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">working</span>       green               color of system running smoothly
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">edit</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">cell</span>     white               cell color to use when editing cell
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">edit</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">fill</span>      _                   edit field fill character
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">unprintable</span>    ·                   substitute character for unprintables
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">histogram</span>      *                   histogram element character
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">histolen</span>       50                  width of histogram column
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">replay</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">play</span>    ▶                   status indicator for active replay
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">replay</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pause</span>   ‖                   status indicator for paused replay
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">status</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">replay</span> green               color of replay status indicator
     <span style="font-weight:bold;">disp</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pixel</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">random</span>   False               randomly choose attr from set of pixels instead of most common
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">graph</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">hidden</span>  238 blue            color of legend for hidden attribute
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">graph</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">selected</span> bold               color of selected graph points
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">graph</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">axis</span>    bold                color for graph axis labels
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">add</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pending</span>   green               color for rows pending add
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">change</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pending</span> reverse yellow     color for cells pending modification
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">delete</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">pending</span> red                color for rows pending delete
     <span style="font-weight:bold;">color</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">xword</span><span style="text-decoration:underline;">_</span><span style="font-weight:bold;">active</span>  green               color of active clue

<span style="font-weight:bold;">EXAMPLES</span>
           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">foo.tsv</span>
     open the file foo.tsv in the current directory

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">-f</span> <span style="font-weight:bold;">sqlite</span> <span style="font-weight:bold;">bar.db</span>
     open the file bar.db as a sqlite database

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">foo.tsv</span> <span style="font-weight:bold;">-n</span> <span style="font-weight:bold;">-f</span> <span style="font-weight:bold;">sqlite</span> <span style="font-weight:bold;">bar.db</span>
     open foo.tsv as tsv and bar.db as a sqlite database

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">-f</span> <span style="font-weight:bold;">sqlite</span> <span style="font-weight:bold;">foo.tsv</span> <span style="font-weight:bold;">bar.db</span>
     open both foo.tsv and bar.db as a sqlite database

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">-b</span> <span style="font-weight:bold;">countries.fixed</span> <span style="font-weight:bold;">-o</span> <span style="font-weight:bold;">countries.tsv</span>
     convert countries.fixed (in fixed width format) to countries.tsv (in tsv format)

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">postgres://</span><span style="text-decoration:underline;">username</span><span style="font-weight:bold;">:</span><span style="text-decoration:underline;">password</span><span style="font-weight:bold;">@</span><span style="text-decoration:underline;">hostname</span><span style="font-weight:bold;">:</span><span style="text-decoration:underline;">port</span><span style="font-weight:bold;">/</span><span style="text-decoration:underline;">database</span>
     open a connection to the given postgres database

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">--play</span> <span style="font-weight:bold;">tests/pivot.vd</span> <span style="font-weight:bold;">--replay-wait</span> <span style="font-weight:bold;">1</span> <span style="font-weight:bold;">--output</span> <span style="font-weight:bold;">tests/pivot.tsv</span>
     replay tests/pivot.vd, waiting 1 second between commands, and output the final sheet to test/pivot.tsv

           <span style="font-weight:bold;">ls</span> <span style="font-weight:bold;">-l</span> | <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">-f</span> <span style="font-weight:bold;">fixed</span> <span style="font-weight:bold;">--skip</span> <span style="font-weight:bold;">1</span> <span style="font-weight:bold;">--header</span> <span style="font-weight:bold;">0</span>
     parse the output of ls -l into usable data

           <span style="font-weight:bold;">ls</span> | <span style="font-weight:bold;">vd</span> | <span style="font-weight:bold;">lpr</span>
     interactively select a list of filenames to send to the printer

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">newfile.tsv</span>
     open a blank sheet named <span style="text-decoration:underline;">newfile</span> if file does not exist

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">sample.xlsx</span> <span style="font-weight:bold;">+:sheet1:2:3</span>
     launch with <span style="font-weight:bold;">sheet1</span> at top-of-stack, and cursor at column <span style="font-weight:bold;">2</span> and row <span style="font-weight:bold;">3</span>

           <span style="font-weight:bold;">vd</span> <span style="font-weight:bold;">-P</span> <span style="font-weight:bold;">open-plugins</span>
     preplay longname <span style="font-weight:bold;">open-plugins</span> before starting the session

<span style="font-weight:bold;">FILES</span>
     At the start of every session, <span style="font-weight:bold;">VisiData</span> looks for <span style="text-decoration:underline;">$HOME/.visidatarc</span>, and calls Python exec() on its contents if it exists. For example:

        options.min_memory_mb=100  # stop processing without 100MB free

        bindkey('0', 'go-leftmost')   # alias '0' to go to first column, like vim

        def median(values):
            L = sorted(values)
            return L[len(L)//2]

        aggregator('median', median)

     Functions defined in .visidatarc are available in python expressions (e.g. in derived columns).

<span style="font-weight:bold;">SUPPORTED</span> <span style="font-weight:bold;">SOURCES</span>
     Core VisiData includes these sources:

        <span style="font-weight:bold;">tsv</span> (tab-separated value)
           Plain and simple. <span style="font-weight:bold;">VisiData</span> writes tsv format by default. See the <span style="font-weight:bold;">--tsv-delimiter</span> option.

        <span style="font-weight:bold;">csv</span> (comma-separated value)
           .csv files are a scourge upon the earth, and still regrettably common.
           See the <span style="font-weight:bold;">--csv-dialect</span>, <span style="font-weight:bold;">--csv-delimiter</span>, <span style="font-weight:bold;">--csv-quotechar</span>, and <span style="font-weight:bold;">--csv-skipinitialspace</span> options.
           Accepted dialects are <span style="font-weight:bold;">excel-tab</span>, <span style="font-weight:bold;">unix</span>, and <span style="font-weight:bold;">excel</span>.

        <span style="font-weight:bold;">fixed</span> (fixed width text)
           Columns are autodetected from the first 1000 rows (adjustable with <span style="font-weight:bold;">--fixed-rows</span>).

        <span style="font-weight:bold;">json</span> (single object) and <span style="font-weight:bold;">jsonl</span>/<span style="font-weight:bold;">ndjson</span>/<span style="font-weight:bold;">ldjson</span> (one object per line).
           Cells containing lists (e.g. <span style="font-weight:bold;">[3]</span>) or dicts (<span style="font-weight:bold;">{3}</span>) can be expanded into new columns with <span style="font-weight:bold;">(</span> and unexpanded with <span style="font-weight:bold;">)</span>.

        <span style="font-weight:bold;">sqlite</span>
           May include multiple tables. The initial sheet is the table directory; <span style="font-weight:bold;">Enter</span> loads the entire table into memory. <span style="font-weight:bold;">z^S</span> saves modifications to source.

     URL schemes are also supported:
        <span style="font-weight:bold;">http</span> (requires <span style="font-weight:bold;">requests</span>); can be used as transport for with another filetype

     For a list of all remaining formats supported by VisiData, see https://visidata.org/formats.

     In addition, <span style="font-weight:bold;">.zip</span>, <span style="font-weight:bold;">.gz</span>, <span style="font-weight:bold;">.bz2</span>, and <span style="font-weight:bold;">.xz</span> files are decompressed on the fly.

<span style="font-weight:bold;">SUPPORTED</span> <span style="font-weight:bold;">OUTPUT</span> <span style="font-weight:bold;">FORMATS</span>
     These are the supported savers:

        <span style="font-weight:bold;">tsv</span> (tab-separated value)
        <span style="font-weight:bold;">csv</span> (comma-separated value)
        <span style="font-weight:bold;">json</span> (one object with all rows)
        <span style="font-weight:bold;">jsonl</span>/<span style="font-weight:bold;">ndjson</span>/<span style="font-weight:bold;">ldjson</span> (one object per line/row)
           All expanded subcolumns must be closed (with <span style="font-weight:bold;">)</span>) to retain the same structure.
        <span style="font-weight:bold;">sqlite</span> (save to source with <span style="font-weight:bold;">z^S</span>)
        <span style="font-weight:bold;">md</span> (markdown table)

<span style="font-weight:bold;">AUTHOR</span>
     <span style="font-weight:bold;">VisiData</span> was made by Saul Pwanson &lt;<span style="text-decoration:underline;">vd@saul.pw</span>&gt;.

Linux/MacOS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       Apr 11, 2021                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      Linux/MacOS
</pre>