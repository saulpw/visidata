# VisiData Plugin Authors Guide
### VisiData Version: v2.0
### Date: 2020-09

0. Notes
- In general, method names without underscores (usually camelCase) are public API
- method names with leading underscore are private to file.
- method names with embedded underscore are private to visidata internals.

Function signatures are do not include the leading self argument, whether vd or sheet or col or otherwise.  is listed 



1. Customizing
  - Options
  - Commands
  - Extensible

2. Loading and Saving
  - writing a loader

3. Core
  - VisiData, Sheet, Column
  - Compute
     - Cell, Value, DisplayValue
     - Types
     - Null
     - Errors
  - Expressions

4. Interface
  - Terminal
     - Colors
  - Cursor
  - Layout
  - Input/Edit
  - Status

5. User Concepts
  - Keys
  - Selection
  - Undo
  - Command Log and Replay

  - Aggregators
  - Sorting

6. Modifying Data
  - calc vs. get
  - put vs. set
  - commit

7. Plotting
  - Canvas, Graph

8. Performance
  - Async
  - Caches

9. Miscellaneous
  - fetching external resources


include options.md
include commands.md
include extensible.md
include loaders.md
include core.md
include compute.md
include expr.md
include interface.md
include data.md
include modify.md
include plot.md
include perf.md
include misc.md

