# VisiData Documentation

## Getting started

* [VisiData video demo](https://youtu.be/N1CBDTgGtOU)
* [Installation](/install)

## Tutorials

* Beginner: [An Introduction to VisiData](https://jsvine.github.io/intro-to-visidata/) by [Jeremy Singer-Vine](https://www.jsvine.com/)
* Beginner: [Guida VisiData](https://github.com/ondata/guidaVisiData/tree/master/testo) by [Andrea Borruso](https://medium.com/@aborruso) (onData association)
* Intermediate/Advanced (English): [VisiData case study videos](https://www.youtube.com/watch?v=yhunJc8Nu4g&list=PLxu7QdBkC7drrAGfYzatPGVHIpv4Et46W&index=4) by creator [Saul Pwanson](http://saul.pw)

## References

* [quick reference guide for 2.0](/man)
    * all available commands and options
    * also available as a manpage via `man vd` and from inside VisiData with `Ctrl+H`
* [quick reference guide for 1.5.2](/docs/v1.5.2/man)
* [VisiData Cheat Sheet](https://jsvine.github.io/visidata-cheat-sheet/en/)
* [keyboard layout of commands](/docs/kblayout)

## 'How to' recipes

* [Loading Data](/docs/loading)
    * [Specifying a source file](/docs/loading#specifying-a-source-file)
    * [Loading sources supported by pandas](/docs/loading#loading-sources-supported-by-pandas)
    * [Opening an R data frame with VisiData](/docs/loading#opening-an-r-data-frame-with-visidata)
    * [Loading multiple datasets simultaneously](/docs/loading#loading-multiple-datasets-simultaneously)
    * [Accessing other loaded or derived sheets](/docs/loading#accessing-other-loaded-or-derived-sheets)
    * [Converting a dataset from one supported filetype into another](/docs/loading#convert)
* [Navigation](/docs/navigate)
    * How to rapidly scroll through a sheet
    * How to search within a sheet
    * How to move between sheets
* [Rows](/docs/rows)
    * How to perform operations on a subset of rows
    * How to filter rows
    * How to filter a random subset of rows
    * How to move, copy and remove rows
    * How to sort rows
* [Columns](/docs/columns)
    * How to manipulate columns
    * How to hide (remove) and unhide columns
    * How to specify column types
    * How to split a column
    * How to expand columns that contain nested data
    * How to create derivative columns
    * How to configure multiple columns
* [Editing contents](/docs/edit)
    * How to edit cells
    * How to rename columns
* [Grouping data and descriptive statistics](/docs/group)
    * How to set statistical aggregators
    * How to create a pivot table
    * How to create a frequency chart
    * How to calculate descriptive statistics
    * How to filter for grouped or described rows
* [Creating sheets, rows and columns](/docs/crud)
    * How to configure the cursor to move right after a successful edit
    * How to set up a sheet for data collection
    * How to add a new blank column
    * How to fill a column with a range of numbers
* [Combining datasets](/docs/join)
    * How to perform a join
    * How to append two datasets
* [Drawing graphs](/docs/graph)
    * How to graph a single column
    * How to graph multiple columns
    * How to interact with graphs
* [How to save and replay a VisiData session](/docs/save-restore)
* [Customizing VisiData](/docs/customize)
    * How to configure VisiData (user)
    * How to configure VisiData (dev)
    * How to have configurations persist
    * How to configure commands
* [Plugins - extending VisiData functionality](/docs/plugins)
* [Developing a loader](/docs/api/loaders)
* [STDOUT pipe/redirect](/docs/pipes)

# For developers

VisiData can interact with data from any source or in any format.
* [VisiData API Guide](/docs/api)
* [guide to contributing](/contributing)
* [viewtsv annotated](/docs/viewtsv)
