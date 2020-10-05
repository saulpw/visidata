.. _performance:

=========================
Threads
=========================

VisiData is not necessarily the fastest at processing large amounts of data, but great care has been taken to make sure that it remains *responsive*.
It is better to wait 10 seconds with active indication of progress, than 2 seconds with the program frozen and not accepting input (or worse; queueing up commands without ability to cancel).

To this end, VisiData has a main interface thread for display and input, and creates threads for any task that may be time-consuming.
In fact, anything that iterates through all rows (there may be millions) or all columns (there may be thousands), should probably be in its own thread.

``@asyncthread``
~~~~~~~~~~~~~~~~

Use the ``@asyncthread`` decorator on a function to spawn a new thread for each call to that function.
The return value is the spawned thread (which can often be ignored by the caller), and the return value of the original function is effectively lost.

Cells which are being computed in a separate thread will have the Thread object as their value until the result is available.
[This will show the ``options.disp_pending`` cell note and allow the user to interact with the specific thread (via e.g. :kbd:`z Ctrl+Y` or :kbd:`z Ctrl+C`).]

Each thread is added to ``Sheet.currentThreads`` on the current sheet, and to ``vd.threads``.
Note that a thread spawned by calling a function on a different sheet will add the thread to the currentThreads for the topmost/current sheet instead.

.. autoclass:: visidata.asyncthread

.. data:: visidata.vd.threads

A list of all threads.

.. data:: visidata.BaseSheet.currentThreads

A list of all threads started from commands on this sheet.

.. autofunction:: visidata.vd.execAsync
.. autofunction:: visidata.vd.sync
.. autofunction:: visidata.vd.cancelThread

.. note::

    ``vd.cancelThread(*threads)`` sends each thread an ``EscapeException``, which percolates up the stack to be caught by the thread entry point.
    ``EscapeException`` inherits from Python's ``BaseException`` instead of ``Exception``, so that functions can still have catchall try-blocks with ``except Exception:``, without catching explicit user cancellations.

    An unqualified ``except:`` clause is bad practice (as always).
    When used in an async function, it will make the thread uncancelable.

.. _progress:

Progress counters
~~~~~~~~~~~~~~~~~~

To provide the progress meter in the right status bar, every function that could iterate over a large collection of objects (usually rows or columns) or loop a large number of times, should use an ``Progress`` object somewhere to track its progress.

.. note::

    Many internal functions will contribute their own ``Progress`` counters (including ``visidata.Path.read``), so an async function may not need its own, but it can still be helpful to provide a more precise *gerund* to show to the user.

.. autoclass:: visidata.vd.Progress

.. function:: visidata.vd.Progress.addProgress(n)

    Increase the progress count by *n*.


Progress as iterable
^^^^^^^^^^^^^^^^^^^^^

When iterating over a potentially large sequence:

::

    for item in Progress(iterable, gerund='working'):

This is equivalent to ``for item in iterable``.  The `gerund` specifies the action being performed.

- These ``Progress`` only display if used in another thread, and has no effect otherwise.  So any iteration over rows and columns should have ``Progress``, even if it is not ``@asyncthread``.
- Use ``Progress`` around the innermost iterations for maximum precision in the progress meter.
- But this incurs a small amount of overhead, so if a tight loop needs every last optimization, use it with an outer iterator instead.
- Multiple ``Progress`` objects used in parallel will stack properly.
- Multiple ``Progress`` objects used serially will make the progress indicator reset (which is better than having no indicator at all).

If *iterable* does not know its own length, then pass the length or an approximation as the *total* keyword argument:

::

    for item in Progress(iterable, gerund='working', total=approx_size):

Each iteration of the ``Progress`` object contributes 1 towards the total.
To contribute a different amount, use ``Progress.addProgress(n)`` (n-1 if being used as an iterable, as 1 will be added automatically).

Progress as context manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To manage ``Progress`` without wrapping an iterable, use it as a context manager with only a ``total`` keyword argument, and call ``addProgress`` as progress is made:

::

    with Progress(gerund='working', total=amt) as prog:
        while amt > 0:
            some_amount = some_work()
            prog.addProgress(some_amount)
            amt -= some_amount

- Using ``Progress`` other than as an iterable or a context manager will have no effect.




Threads Sheet
~~~~~~~~~~~~~~

The Threads Sheet is useful for analyzing the performance of long-running async commands.

All threads (active, aborted, and completed) are added to ``vd.threads``, which can be viewed as the ThreadsSheet via :kbd:`Ctrl+T`.
Threads which take very little time (currently less than 10ms) are removed, to reduce clutter.

- Press :kbd:`Ctrl+_` (*toggle-profile*) to toggle profiling of the main thread.
- Press :kbd:`Enter` (*open-row*) on a thread to view its performance profile (if ``options.profile`` was set when the thread started).

Profiling
^^^^^^^^^

The performance profile sheet in VisiData is the output from ``pstats.Stats.print_stats()``.

- :kbd:`z Ctrl+S` on the performance profile will call ``dump_stats()`` and save the profile data to the given filename, for analysis with e.g. `pyprof2calltree <https://libraries.io/pypi/pyprof2calltree>`__ and `kcachegrind <https://kcachegrind.github.io/html/Home.html>`__.
