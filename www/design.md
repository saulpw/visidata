## The Design of VisiData: Foundations

0. [About Visidata](/about)
1. [Architecture Overview](/design/overview)
2. [Design Goals](/design/goals)
3. [Sheets](/design/sheets)
  a. [Sources]
  b. [Cursor]()
  c. [Columns]()
  d. [Compute]()
  e. [Display]()
4. [Display and Computation Engine](/design/engine)
4. [Commands](/design/commands)
  a. [Python integration](/design/commands#python)
  b. [Errors](/design/commands#errors)
  c. [Status](/design/commands#status)
5. [Command Log](/design/commandlog)
6. [Loaders](/design/loaders)
7. [Hooks](/design/hooks)
8. [Row selection](/design/selected)
9. [@async](/design/async)
10. [Colorizers](/design/color)
11. [Options](/design/options)
A. [Builtin line editor](/design/editor)
B. [API Reference](/design/api)

## The Design of VisiData, Part 2: Derived Sheets

2. [Frequency Table]()
3. [Aggregators](/design/aggregators)
4. [Pivot]()
5. [Describe]()

5. [Graph]()
6. [Map](/design/)

## The Design of VisiData, Part 3: Custom Applications

1. [How to make a sheet](/howto/sheet)

## License

The core `vdtui` module is a single-file standalone framework, [available for reuse](/design/vdtui) according to the MIT open-source license.
This is to encourage a profileration of modern terminal user interfaces for any and every application.

The rest of VisiData (anything in the [saulpw/visidata](http://github.com/saulpw/visidata) repository) is licensed under GPL3.
This is to encourage public extensions.
Every additional loader and transformation unlocks latent power within the Python ecosystem.
