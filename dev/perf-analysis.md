# How to analyze performance issues in VisiData

## 1. Find a reliable repro (usually a large or pathological dataset).

Many perf issues will require a dataset with a large number of rows.
Other perf issues involve extremes of data besides raw dataset size: 1000s of columns, or very deep nesting, or very long values.
The rest involve environmental extremes: a huge terminal window, 

We're generally not interested in optimizing for pathological cases, especially if it makes the program a lot more complicated, or degrades more general functionality.
VisiData should not crash or become so unresponsive that it needs to be killed, but it's not meant to handle 10+ million rows.  Get a subset of the data first, or use a more specialized tool.  Maybe `vdsql`.

However, VisiData should be able to handle 1 million rows (1GB of data) reasonably well.  So find a dataset of that size or smaller which exhibits the performance problem.

## 2. Enable profiling and then run the command.

Enable profiling with `Ctrl+_` and run the command with the performance problem.
If it's a small problem (under a few seconds), you may have to run the command
several times in rapid succession.

If profiling the main interface thread, then launch visidata with `--profile` to enable it from the start.

To profile startup time, run:

    time python -m cProfile -o startup-vd.pyprof bin/vd -N

and then press `gq` or `Ctrl+Q` as quickly as possible.

Note: you'll have to comment out `curses.flushinp()` in `mainloop.py` to not discard these keystrokes.
Also, comment out `os._exit(rc)` in `main.py` so that cProfile can save its profiling data.

This will profile the time between pressing Enter on the CLI and the first command processed.  The total time is the last number given by `time`, in seconds:

    0.34s user 0.04s system 100% cpu 0.374 total

The total startup-to-quit time should be under 250ms (and if possible under 100ms).  (Here it is 374ms).


## 3. Go to the Threads Sheet and open the profile of the slow thread.

Wait until the profiled command has finished running, then press `Ctrl+T` to open the Threads Sheet and find the profiled thread.  Look for a thread with a `profile` entry and high `process_time`.

Most long-running commands should already be spawning a new thread.  If the problem is in the interface thread (evidenced by laggy commands, or "freezing" while running a command), then you'll have to launch with `--profile` and look at the MainThread.

## 4. Press `Enter` on that thread to see the captured profile.

This is structured output like you might see from a standard Python profiling tool.
In fact, you can save the profile data to a `.pyprof` file with `z Ctrl+S` and analyze it with other tools.  I often do this (after saving to `foo.pyprof`):

```
    pyprof2calltree -i foo.pyprof -o foo.kcachegrind
    kcachegrind foo.kcachegrind
```

This requires the [pyprof2calltree](https://github.com/pwaller/pyprof2calltree/) and [kcachegrind](https://kcachegrind.github.io/html/Home.html) tools.  There are many others; choose your favorite.

## 5.  Or you can analyze it from within VisiData.

Sort descending by `totaltime_us` first to find the largest toplevel consumers of time.  The first one or few should be obvious (the overall command itself), but after that it should show which parts of the command are taking up most of the time.

Then you can sort descending by `inlinetime_us` to find the largest lowlevel consumers.

Press `Ctrl+O` to open the current function in an editor.

In general, look for non-trivial functions with a large `callcount` with `inlinetime_us` that accounts for a significant fraction of the total time; these are hotspots that are ripe for optimization.

If no single call is taking up more than 50% of the command time, optimization is going to be more difficult.  In these cases, focus on eliminating or delaying unnecessary work, or providing feedback about progress.  It's more important for VisiData to be lazy and responsive than to do a huge amount of work as quickly as possible.

## 6. Try out an optimization and remeasure.

If a small optimization results in a measurable performance improvement, it's a keeper.  Otherwise, ditch it.  Go back to step 2 until performance is adequate.
