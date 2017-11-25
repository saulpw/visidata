# Terminal Graphics in VisiData

VisiData can display low-resolution terminal graphics with a reasonable amount of user interactivity.

The current implementation uses braille Unicode characters (inspired by [asciimoo/drawille](https://github.com/asciimoo/drawille)).  The [sixel protocol](https://en.wikipedia.org/wiki/Sixel) may be supported in the future.

## Class hierarchy

- `Sheet`: the drawable context base class
- `Plotter`: pixel-addressable display of entire terminal with (x,y) integer pixel coordinates
- `Canvas`: zoomable/scrollable virtual canvas with (x,y) coordinates in arbitrary units
- `InvertedCanvas`: a canvas with inverted y-axis
- `Graph`: axis labels, a legend, and gridlines

### Summary

The async `Graph.reload()` iterates over the given `sourceRows` (from its `source` [`Table`](/design/table)) and calls `Canvas.polyline()` to indicate what to render.  `Canvas.refresh()` triggers an async `Canvas.render()`, which iterates over the polylines and labels and calls `Plotter.plot*` methods.  The `run()` loop calls `Plotter.draw()`, which determines the characters and colors to represent the pixels.

### class `Plotter`

A `Plotter` is a [`Sheet`](/design/sheet) with a pixel-addressable drawing surface that covers the entire terminal (minus the status line).  Pixels and labels are plotted at exact locations on the screen. 

`Plotter.draw(scr)` is called multiple times per second to update the screen, and chooses an attr for each pixel.
By default, the most common attr is chosen for each pixel, but if `options.disp_pixel_random` is set, an attr will be randomly chosen (weighted naturally).  This may cause pixels to flicker between their possible attrs.
If an attr is in the `hiddenattrs` set, then it is not considered for display at all.

All Plotter coordinates should be integer numbers of pixels.
For performance reasons, they are presumed to already be integers, to save unnecessary calls to `round()`.
Methods which plot multiple pixels on the canvas should be careful to gauge the display correctly; simply calling `round()` on each calculated float coordinate will work but can cause display artifacts.

#### `Plotter` methods

For Plotter methods, x and y must be integers, where `0 <= x < plotwidth`, and `0 <= y < plotheight`.  `(0,0)` is in the upper-left corner of the terminal window.

Pixels can be plotted directly onto a Plotter with:

- `Plotter.plotpixel(x, y, attr, row=None)`
- `Plotter.plotline(x1, y1, x2, y2, attr, row=None)`
- `Plotter.plotlabel(x, y, text, attr)`

The above `plot*` methods append the `row` to `Plotter.pixels[y][x][attr]`.

`attr` is a [curses attribute](/design/color), and `row` is the object associated with the pixel.

These properties and methods are also available:

- `Plotter.plotwidth` is the width of the terminal, in pixels.
- `Plotter.plotheight` is the height of the terminal, in pixels.
- `Plotter.rowswithin(x1, y1, x2, y2)` generates the rows plotted within the given region.
- `Plotter.toggleattr(attr)` adds attr to `hiddenattrs` if not there already, or removes it if it is.
- `Plotter.refresh()` is called whenever the screen size changes, and should also be invoked whenever new content is added.

### class `Canvas`

A **`Canvas`** is a `Plotter` with a virtual surface on which lines and labels can be rendered in arbitrary units.

The onscreen portion (the area within the visible bounds) is scaled and rendered onto the `Plotter`, with the minimum coordinates in the upper-left [same orientation as `Plotter`].

The [`Canvas` user interface](/howto/graph#commands) supports zoom, scroll, cursor definition, and selection of the underlying rows.  The `source` attribute should be the Table which owns the plotted `row` objects.

A call to `Canvas.refresh()` will trigger `Canvas.render()`, which is decorated with `@async` as it may take a few seconds for large datasets.  Any active `render` threads are cancelled first.

#### `Canvas` methods

- `Canvas.polyline(vertices, attr, row=None)` adds a multi-segment line from the list of (x,y) `vertices`.  One vertex draws a point; two vertices draws a single line.
- `Canvas.label(xy, text, attr, row=None)` adds `text` at `xy` in canvas units.
- `Canvas.fix(xyplotter, xycanvas)` sets `visibleMinXY` so that `xycanvas` is plotted at `xyplotter`.
- `Canvas.zoom(xymin, xymax)` sets the visible bounds so the given canvas coordinates will fill the entire Plotter area.  `aspectratio` will still be obeyed.
- `Canvas.keyattr(key)` returns the `attr` for the given `key`, assigning a new color from `options.plot_colors` if `key` has not been seen before.  These keys are plotted as legends on the upper right corner of the canvas.  The last color is given out for all remaining keys and is labeled `other`.
- `Canvas.resetBounds()` needs to be called after some or all points have been rendered, but before anything can be plotted.  It initializes the width and height of the canvas, visible area, and/or cursor.
- `Canvas.reset()` clears the canvas in preparation for `reload()`.

#### `Canvas` properties

- The *canvas bounds* reflect the bounds of the entire canvas:
    - `Canvas.canvasMinXY` is the minimum (x,y).
    - `Canvas.canvasMaxXY` is the maximum (x,y).
    - `Canvas.canvasWH` is the (width,height).
- The *visible bounds* define the onscreen canvas area:
    - `Canvas.visibleMinXY` is the minimum (x,y).
    - `Canvas.visibleMaxXY` is the maximum (x,y).
    - `Canvas.visibleWH` is the (width,height).
- The *cursor bounds* define the cursor region in canvas coordinates:
    - `Canvas.cursorMinXY` is the minimum (x,y).
    - `Canvas.cursorMaxXY` is the maximum (x,y).
    - `Canvas.cursorWH` is the (width,height).

- `Canvas.zoomlevel` is a settable property, which sets the `visibleWH` accordingly.  `zoomlevel` of 1.0 makes the entire canvas visible.  Does not change the `visibleMinXY`.
- `Canvas.aspectratio`, if set, maintains a proportional `visibleWH` (considering also `plotwidth/plotheight`).  `aspectratio` of 1.0 should be square.
- `Canvas.charWH` is the (width,height) of one terminal character, in canvas units.
- `Canvas.centerXY` is the (x,y) of the center of the canvas, in canvas coordinates.

During a [mouse event](/design/commands#mouse), these properties indicate the (x,y) position of the mouse cursor:

- `Canvas.canvasMouseXY` in canvas coordinates
- `Plotter.plotterMouseXY` in plotter (pixel) coordinates
- `Sheet.charMouseXY` in curses (character) coordinates

### class `InvertedCanvas`

An `InvertedCanvas` is a `Canvas` with a few internal methods overridden, such that the Y axis is inverted.  For an `InvertedCanvas`, the minimum coordinates are in the lower-left.

`InvertedCanvas` has not much else of interest.  It should be completely interchangeable with `Canvas`.

### class `Graph`

A `Graph` is an `InvertedCanvas` with axis labels and/or gridlines.

- `Graph.__init__(name, sheet, rows, xcols, ycols)` constructor
    - `sheet` is the source Table
    - `rows` is a list of the rows to iterate over
    - `xcols` is a list of key columns forming the x-axis and color keys
    - `ycols` is a list of numeric columns to be plotted on the y-axs

---
