
# Maintaining a responsive interface

## `@async`

Use the `@async` decorator on a function to make it execute in a thread.
The return value is the spawned thread (which can often be ignored by the caller); the return value of the original function is effectively lost.

Cells which are being computed in a separate thread should have that thread as their value until their result is available.
This will show the `options.disp_pending` notation and allow the user to interact with the specific thread (via e.g. `z^Y` and others).

Each thread is added to `Sheet.currentThreads` for the current sheet.
Note that a thread spawned by calling a function on a different sheet will add the thread to the currentThreads for the topmost/current sheet instead.

### Canceling threads

The user can cancel all `Sheet.currentThreads` with `^C`.

Internally, `cancelThread(*threads)` will send each thread an `EscapeException`, which percolates up the stack to be caught by the thread entry point.
EscapeException inherits from BaseException instead of Exception, so that threads can still have catch-all try blocks with `except Exception:`.
An unqualified `except:` clause is bad practice (as always); when used in an async function, it will make the thread uncancelable.

### Wait for threads to finish

`sync(expectedThreads)` will wait for all but `expectedThreads` to finish.

This will only rarely be useful.

# Threads Sheet (`^T`)

All threads (active, aborted, and completed) are added to `VisiData.threads`, which can be viewed as the Task Sheets via `^T`.
Threads which take less than `min_task_time_s` (hardcoded in `async.py` to 10ms) are removed, to reduce clutter.

- Press `ENTER` (on the Threads Sheet) on a thread to view its performance profile (if `options.profile_tasks` was True when the thread started).
- Press `^_` (anywhere) to toggle profiling of the main thread.

## Profiling

The view of a performance profile in VisiData is the output from `pstats.Stats.print_stats()`.
- `z^S` on the performance profile will call `dump_stats()` and save the profile data to the given filename, for analysis with e.g. [pyprof2calltree]() and [kcachegrind]().
- (`z^S` because the raw text can be saved with `^S` as usual.  Ideally, `^S` to a file with a `.pyprof` extension on a profile sheet would do this instead.)

# Progress

In `@async` functions, use `Progress` to easily provide a progress indicator for the user.

## Progress as iterable

When iterating over a potentially large sequence:

```
for item in Progress(iterable):
```

This is just like `for item in iterable`, but it also keeps track of progress, to display on the right status line.
- This only displays if used in another thread (but is harmless if not).
- Use Progress around the innermost iterations for maximum granularity and apparent responsiveness.
- But this incurs a small amount of overhead, so if a tight loop needs every last optimization, use it with an outer iterator instead (if there is one).
- Using Progress on multiple iterators in sequence will make the progress indicator reset (which is better than having no indicator).

If `iterable` does not know its own length, it (or an approximation) should be passed as the `total` kwarg:

```
for item in Progress(iterable, total=approx_size):
```

The `Progress` object contributes 1 towards the total for each iteration.
To contribute a different amount, use `Progress.addProgress(n)` (n-1 if being used as an iterable, as 1 will be added automatically).

## Progress as context handler

To manage `Progress` without wrapping an iterable, use it as a context handler with only a `total` kwarg, and call `addProgress` as progress is made:

```
with Progress(total=amt) as prog:
    while amt > 0:
        some_amount = some_work()
        prog.addProgress(some_amount)
        amt -= some_amount
```

- Using Progress() other than as an iterable or a context manager will have no effect.

---
