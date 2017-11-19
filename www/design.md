## The Design of VisiData: Foundations {#TOC}

0. [About Visidata](/about)
1. [Architecture Overview](/design/overview)
2. [Design Goals](/design/goals)
3. [Sheets](/design/sheets)
    i. [Sources]
    ii. [Cursor]()
    iii. [Columns]()
    iv. [Compute]()
    v. [Display]()
4. [Display and Computation Engine](/design/engine)
5. [Commands](/design/commands)
    i. [Python integration](/design/commands#python)
    ii. [Errors](/design/commands#errors)
    iii. [Status](/design/commands#status)
6. [Command Log](/design/commandlog)
7. [Loaders](/design/loaders)
8. [Hooks](/design/hooks)
9. [Row selection](/design/selected)
10. [@async](/design/async)
11. [Colorizers](/design/color)
12. [Options](/design/options)
    i. [Builtin line editor](/design/editor)
    ii. [API Reference](/design/api)

<!-- end of list -->

## The Design of VisiData, Part 2: Derived Sheets {#TOC}

1. [Frequency Table]()
2. [Aggregators](/design/aggregators)
3. [Pivot]()
4. [Describe]()
5. [Graph]()
6. [Map](/design/)

<!-- end of list -->

## The Design of VisiData, Part 3: Custom Applications {#TOC}

1. [How to make a sheet](/howto/sheet)

<!-- end of list -->

## License

The core `vdtui` module is a single-file standalone framework, [available for reuse](/design/vdtui) according to the MIT open-source license.
This is to encourage a profileration of modern terminal user interfaces for any and every application.

The rest of VisiData (anything in the [saulpw/visidata](http://github.com/saulpw/visidata) repository) is licensed under GPL3.
This is to encourage public extensions.
Every additional loader and transformation unlocks latent power within the Python ecosystem.
