---
eleventyNavigation:
  key: Terminal Graphics in VisiData
  order: 99
Updated: 2017-12-06
Version: VisiData 1.0
---



VisiData can display low-resolution terminal graphics with a reasonable amount of user interactivity.

The current implementation uses braille Unicode characters (inspired by [asciimoo/drawille](https://github.com/asciimoo/drawille)).  [Unicode blocks](https://en.wikipedia.org/wiki/Block_Elements) or the [sixel protocol](https://en.wikipedia.org/wiki/Sixel) may be supported in the future.

## Class hierarchy

- `Sheet`: the drawable context base class (part of core vdtui.py)
- `Plotter`: pixel-addressable display of entire terminal with (x,y) integer pixel coordinates
- `Canvas`: zoomable/scrollable virtual canvas with (x,y) coordinates in arbitrary units
- `InvertedCanvas`: a Canvas with inverted y-axis
- `Graph`: an InvertedCanvas with axis labels, a legend, and gridlines

### Summary

- The async `Graph.reload()` iterates over the given `sourceRows` (from its `source` Sheet) and calls `Canvas.polyline()` to indicate what to render.
- `Canvas.refresh()` triggers an async `Canvas.render()`, which iterates over the polylines and labels and calls the `Plotter.plot*` methods. 
- The `VisiData.run()` loop calls `Plotter.draw()`, which determines the characters and colors to represent the pixels.

### class `Plotter`

A `Plotter` is a [`Sheet`](/design/sheet) with a pixel-addressable drawing surface that covers the entire terminal (minus the status line).  Pixels and labels are plotted at exact locations in the terminal window, and must be recalculated after any zoomlevel change or terminal resizing.

`Plotter.draw(scr)` is called multiple times per second to update the screen, and chooses a curses attribute for each pixel.
By default, the most common attr is chosen for each pixel, but if `options.disp_graph_pixel_random` is set, an attr will be randomly chosen from the naturally weighted set of attrs (this may cause blocks of pixels to flicker between their possible attrs).
If an attr is in the `Canvas.hiddenAttrs` set, then it is not considered for display at all (and its rows will be ignored during selection).

All Plotter coordinates must be integer numbers of pixels.
[For performance reasons, they are presumed to already be integers, to save unnecessary calls to `round()`.]
Methods which plot multiple pixels on the canvas should be careful to gauge the display correctly; simply calling `round()` on each calculated float coordinate will work but can cause display artifacts.

#### `Plotter` methods

For Plotter methods, `x` and `y` must be integers, where `0 <= x < plotwidth`, and `0 <= y < plotheight`.  `(0,0)` is in the upper-left corner of the terminal window.

Pixels can be plotted directly onto a Plotter with these methods:

- `Plotter.plotpixel(x, y, attr, row=None)`
- `Plotter.plotline(x1, y1, x2, y2, attr, row=None)`
- `Plotter.plotlabel(x, y, text, attr)`

`attr` is a [curses attribute](/design/color), and `row` is the object associated with the pixel.

The above `plot*` methods append the `row` to `Plotter.pixels[y][x][attr]`.

These properties and methods are also available:

- `Plotter.plotwidth` is the width of the terminal, in pixels.
- `Plotter.plotheight` is the height of the terminal, in pixels.
- `Plotter.rowsWithin(bbox)` generates the rows plotted within the given region.
- `Plotter.hideAttr(attr, hide=True)` adds attr to `hiddenAttrs` if `hide`, and removes it otherwise.
- `Plotter.refresh()` is called whenever the screen size changes, and should also be invoked whenever new content is added.

`rowsWithin` takes a `Box` object (described below).  The `Box` class is otherwise unused by the Plotter.

### class `Canvas`

A **`Canvas`** is a `Plotter` with a virtual surface on which lines and labels can be rendered in arbitrary units.

The onscreen portion (the area within the visible bounds) is scaled and rendered onto the `Plotter`, with the minimum coordinates in the upper-left [same orientation as `Plotter`].

The [`Canvas` user interface](/docs/graph#commands) supports zoom, scroll, cursor definition, and selection of the underlying rows.  The `source` attribute should be the Sheet which owns the plotted `row` objects.

A call to `Canvas.refresh()` will trigger `Canvas.render()`, which is decorated with `@asyncthread` as it may take a perceptible amount of time for larger datasets.  Any active `render` threads are cancelled first.

#### `Box` and `Point` helper classes

While the Plotter API requires literal integer values for `x`/`y` and `width`/`height` parameters, `Canvas` methods generally take float values contained in either `Box` or `Point` classes.

##### `Point`

`Point` is simply a container for an `(x,y)` coordinate (passed to the constructor).  The individual components are stored as `.x` and `.y`, and the computed `.xy` property will return `(x,y)` as a simple tuple.  `Point` can also stringify itself reasonably.

##### `Box`

`Box` is effectively a rectangle stretching over some area of the canvas.  The constructor takes `(x,y,w,h)`, but a `Box` can also be constructed using the `BoundingBox(x1,y1,x2,y2)` helper.  [Note that in the BoundingBox case, the order of the individual points is not guaranteed; the individual coordinates may be swapped for convenience.]

`Box` has these members and properties:

- `xmin` and `ymin`: the minimum coordinates of the area.
- `xmax` and `ymax`: the maximum coordinates of the area.
- `xcenter` and `ycenter`: the central coordinates of the area.
- `w` and `h`: the width and height of the area.
- `xymin`: returns `Point(xmin,ymin)`.
- `center`: returns `Point(xcenter,ycenter)`.
- `contains(x, y)`: returns True if `(x,y)` is inside the bounding box.

#### `Canvas` methods

- `Canvas.polyline(vertices, attr, row=None)` adds a multi-segment line from the list of (x,y) `vertices`.  One vertex draws a point; two vertices draws a single line.  Note that the vertices are *not* Point objects (unlike parameters for other methods).
- `Canvas.label(xy, text, attr, row=None)` adds `text` at `xy` (Point in canvas units).
- `Canvas.fixPoint(xyplotter, xycanvas)` sets the position of the `visibleBox` so that `xycanvas` (Point in Canvas units) is plotted at `xyplotter` (Point in Plotter units).
- `Canvas.zoomTo(bbox)` sets the visible bounds so the given canvas coordinates will fill the entire Plotter area.  `aspectRatio` will still be obeyed.
- `Canvas.keyattr(key)` returns the `attr` for the given `key`, assigning a new color from `options.plot_colors` if `key` has not been seen before.  These keys are plotted as legends on the upper right corner of the canvas.  The last color is given out for all remaining keys and is labeled "other".
- `Canvas.resetBounds()` needs to be called after some or all points have been rendered, but before anything can be plotted.  It initializes the width and height of the canvas, visible area, and/or cursor.
- `Canvas.reset()` clears the canvas in preparation for `reload()`.

#### `Canvas` properties

- `Canvas.canvasBox` reflects the bounds of the entire canvas.
- `Canvas.visibleBox` defines the onscreen canvas area.
- `Canvas.cursorBox` defines the cursor region in canvas coordinates.
- `Canvas.zoomlevel` is a settable property, which sets the `visibleBox` size accordingly.  `zoomlevel` of 1.0 makes the entire canvas visible.  Does not change the position of the `visibleBox` (see `Canvas.fixPoint`).
- `Canvas.aspectRatio`, if set, maintains a proportional width and height of the `visibleBox` (considering also `plotwidth`/`plotheight`).  `aspectRatio` of 1.0 should be square.
- `Canvas.canvasCharWidth` and `Canvas.canvasCharHeight` is the width and height of one terminal character, in canvas units.

These properties reserve an area of the Plotter that is outside the visibleBox:
- `Canvas.leftMarginPixels`
- `Canvas.rightMarginPixels`
- `Canvas.topMarginPixels`
- `Canvas.bottomMarginPixels`

During a [mouse event](/design/commands#mouse), these properties indicate the mouse position for the current mouse event:

- `Canvas.canvasMouse`: a Point in canvas coordinates
- `Plotter.plotterMouse`: a Point in plotter (pixel) coordinates
- `Sheet.mouseX` and `Sheet.mouseY`: individual values in curses (character) coordinates

### class `InvertedCanvas`

An `InvertedCanvas` is a `Canvas` with a few internal methods overridden, such that the Y axis is inverted.  For an `InvertedCanvas`, the minimum coordinates are in the lower-left.

`InvertedCanvas` has not much else of interest.  It should be completely interchangeable with `Canvas`.

### class `Graph`

A `Graph` is an `InvertedCanvas` with axis labels and/or gridlines.

- `Graph.__init__(name, sheet, rows, xcols, ycols)` constructor
    - `sheet` is the `source` Sheet.
    - `rows` is a list of the rows to iterate over (from the given `source`).
    - `xcols` is a list of key columns forming the x-axis and color keys.
    - `ycols` is a list of numeric columns to be plotted on the y-axs.

---
