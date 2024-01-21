---
eleventyNavigation:
    key: Getting Started
    order: 1
---

## Getting started

* [VisiData video demo](https://youtu.be/N1CBDTgGtOU)
* [Installation](/install)

## Tutorials

* Beginner: [An Introduction to VisiData](https://jsvine.github.io/intro-to-visidata/) by [Jeremy Singer-Vine](https://www.jsvine.com/)
* Beginner: [Guida VisiData](https://ondata.github.io/guidaVisiData/) by [Andrea Borruso](https://twitter.com/@aborruso) ([onData association](https://twitter.com/ondatait))
* Intermediate/Advanced (English): [VisiData case study videos](https://www.youtube.com/watch?v=yhunJc8Nu4g&list=PLxu7QdBkC7drrAGfYzatPGVHIpv4Et46W&index=4) by creator [Saul Pwanson](http://saul.pw)

## References

* [quick reference guide](/man)
    * all available commands and options
    * also available as a manpage via `man vd` and from inside VisiData with `Ctrl+H`
* [VisiData Cheat Sheet](https://jsvine.github.io/visidata-cheat-sheet/en/)

## 'How to' recipes

* [Loading Data](/docs/loading)
    * [Specifying a source file](/docs/loading#specifying-a-source-file)
    * [Loading sources supported by pandas](/docs/loading#loading-sources-supported-by-pandas)
    * [Opening an R data frame with VisiData](/docs/loading#opening-an-r-data-frame-with-visidata)
    * [Loading multiple datasets simultaneously](/docs/loading#loading-multiple-datasets-simultaneously)
    * [Accessing other loaded or derived sheets](/docs/loading#accessing-other-loaded-or-derived-sheets)
    * [Converting a dataset from one supported filetype into another](/docs/loading#convert)
* [Navigation](/docs/navigate)
    * rapidly scroll through a sheet
    * search within a sheet
    * move between sheets
* [Rows](/docs/rows)
    * perform operations on a subset of rows
    * filter rows
    * filter a random subset of rows
    * select rows where the current column is not null
    * select rows where the current column is null
    * move, copy and remove rows
    * sort rows
* [Columns](/docs/columns)
    * manipulate columns
    * hide (remove) and unhide columns
    * specify column types
    * split a column
    * expand columns that contain nested data
    * create derivative columns
    * configure multiple columns
* [Editing contents](/docs/edit)
    * edit cells
    * rename columns
* [Grouping data and descriptive statistics](/docs/group)
    * set statistical aggregators
    * create a pivot table
    * create a frequency chart
    * calculate descriptive statistics
    * filter for grouped or described rows
* [Creating sheets, rows and columns](/docs/crud)
    * configure the cursor to move right after a successful edit
    * set up a sheet for data collection
    * add a new blank column
    * fill a column with a range of numbers
* [Combining datasets](/docs/join)
    * perform a join
    * append two datasets
* [Drawing graphs](/docs/graph)
    * graph a single column
    * graph multiple columns
    * interact with graphs
* [How to save and replay a VisiData session](/docs/save-restore)
* [Customizing VisiData](/docs/customize)
    * configure VisiData (user)
    * configure VisiData (dev)
    * have configurations persist
    * configure commands
* [Plugins - extending VisiData functionality](/docs/api/plugins)
* [STDOUT pipe/redirect](/docs/pipes)
