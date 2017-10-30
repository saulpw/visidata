
# VisiData design overview

## What is VisiData?

VisiData is the open source data multitool that I've been developing since 2016.

---
When it comes to data wrangling:

    - Python is a powerful and ubiquitous platform for data processing, transformation and integration;
    - the spreadsheet is an intuitive and flexible paradigm for exploratory analysis;
    - the terminal is an efficient and universal interface with widespread usage;

VisiData unites Python + spreadsheet + terminal into a lightweight tool that scales to gigabytes of data.

You can start using it immediately, and learn new commands as you go.

---

## Primary Motivation

The original impetus was to provide efficient workflows for text mode junkies like myself.

As a data worker, I wanted quick access to data at all stages of the pipeline, with support for all kinds of storage systems and formats.  I wanted to be able to focus on the task at hand, without having to spend unnecessary energy juggling various tools.

# Design Goals

## for Data Engineers and Hackers

- Pragmatic behavior and defaults.
- Expose internals, like error messages and types.
- Optimize for fewest keystrokes.

## Universal Interface

- One interface is sufficient for basic exploration of any kind of tabular data.
- Internals can be viewed with the same interface.

## Lightweight

- Few dependencies, minimal install steps, and no configuration required.
- Launches with minimal delay, all commands feel snappy.
- Easily integratable into existing workflows.
- Workflow substantially faster and smoother than with existing tools.

## Easy workflow customization, experimentation, and prototyping

- Extensible with user-defined commands and views.
- Entire new standalone applications can be created with minimal code.

# The Core Principle: Columns are Functions of Rows

Rows are objects; columns are functions of rows.

Rows can be anything: the actual data of their row, or an index into another data structure.

Columns know how to get (or set) their values, given the row.

Therefore rows can be loaded in whatever format is most convenient or efficient, and Columns are extremely lightweight and composable.
