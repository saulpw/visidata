# Progress

The `Progress` class tracks progress of some task, shown to the user as a percentage in the right status bar.  The progress will not show if the task is run synchronously (because the interface is not updating), so any potentially long-running task should be decorated with `@async`.

If you are just going through a plain iterable whose length is known, then this will indicate the Progress on the given sheet:

```
for r in Progress(sheet, iterable):
    sheet.addRow(r)
```

If the iterable is a generator or something which does not have a length, you can specify or approximate an explicit total, and then use .addProgress(n) to make progress each time through the loop.

A Progress object can also be a context manager, which forcibly sets its
progress to the total when it exits.

```
with Progress(sheet, total=N) as prog:
    while whatever:
        prog.addProgress(1)
```

Multiple Progress() objects will stack correctly.

Every potentially long-running task should have a Progress counter.

Since VisiData has been known to load 10 million rows, and 10 million of anything in Python is at least a few seconds, this means anything linear time [O(n)] or worse should have a Progress counter.


