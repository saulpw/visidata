# Primary Motivation

The original impetus behind VisiData was to provide more efficient workflows for text mode junkies like myself.

As a data worker, I wanted quick access to data at all stages of the pipeline, with support for all kinds of storage systems and formats.
I wanted to be able to focus on the task at hand, without having to spend energy installing or configuring specialized tools just to get a glimpse of the underlying data.

Often I would manage to get what I needed through a combination of UNIX utilities and ad-hoc Python scripts.
But this is like trying to make a microscope from a series of magnifying glasses.

I longed for something more powerful and more efficient.

# Design Goals

## For Data Engineers and Hackers

* Pragmatic behavior and defaults.
* Expose internals, like error messages and types.
* Optimize for fewest keystrokes.

## Universal Interface

* One interface is sufficient for basic exploration of any kind of tabular data.
* Internals can be viewed with the same interface.

## Lightweight

* Few dependencies, minimal install steps, and no configuration required.
* Launches with minimal delay, all commands feel snappy.
* Easily integratable into existing workflows.
* Workflow substantially faster and smoother than with existing tools.

## Easy workflow customization, experimentation, and prototyping

* Extensible with user-defined commands and views.
* Entire new standalone applications can be created with minimal code.

