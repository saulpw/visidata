Documentation
=============

Python Docstrings
-----------------

Functions and methods, classes, and modules normally have standard docstrings.

reStructuredText
----------------

This project uses reStructuredText (in files with extension ``.rst``) because it is more extensible and powerful than Markdown.

Sphinx
------

#. Sphinx is installed via ``pip``. Do initial set-up with ``sphinx-quickstart``. Here we have followed all defaults except creation of a ``.bat`` file::

      > Create Windows command file? (y/n) [y]: n

#. In the auto-populated ``index.rst`` there are three additions to make.

   a. At very the top of the file, add::

         :tocdepth: 2

   b. Change ``:maxdepth: 2`` to ``:maxdepth: 4``.

   c. Below ``:caption: Contents:`` add the name of each file containing documentation::

         home
         user-guide
         dev-guide
         screen-layout
         dev-cursors
         about/contributing
         about/credits

#. In the auto-populated ``conf.py`` you can set the Sphinx them and its options. Themes are listed `on the Sphinx site <http://www.sphinx-doc.org/en/stable/theming.html>`_. Declare a theme by setting ``html_theme`` to a string containing the name of the theme; declare its options by setting ``html_theme_options`` to a dictionary containing key-value pairs for each option, following the page linked to above.

   ``sphinx-quickstart`` defaults to the ``alabaster`` theme. By default, if Sphinx is not used, Read the Docs installs a custom theme called the "`Read the Docs Sphinx Theme <https://github.com/rtfd/sphinx_rtd_theme>`_", which is available via ``pip`` or ``git-clone``. We have installed that theme here. You can create other custom themes using ``INI`` format, as described `on the Sphinx site <http://www.sphinx-doc.org/en/stable/theming.html>`_.

#. ``sphinx-quickstart`` creates a ``Makefile`` in ``docs/``, which will construct HTML straightforwardly::

      make html

#. If ``make`` runs without errors, ``index.html`` will contain your table of contents and documentation. You can now stage, commit, and push the current contents of the repository. 

   Warnings, for instance that a certain ``.rst`` file is not referred to in the documentation, do not seem to cause Sphinx to fail to build.

Read the Docs
-------------

#. In order to use Read the Docs, you need to sign up for an account. The service is free to use, but support may cost money.

#. To import a new project, use the `manual import page of the Dashboard <https://readthedocs.org/dashboard/import/manual/>`_ and click the "Import a Project" button. 

   If you grant Read the Docs admin access to your Git-hosting repository (at https://readthedocs.org/accounts/social/connections/), it will attempt to build a new set of docs each time a commit is pushed, via webhooks. You can also build new docs manually, in the absence of a valid webhook. If a webhook is set up for GitHub, it will be listed on the ``settings => Webhooks`` page of the repository.

#. On the ``Admin`` settings for the project, set "programming language" to Python.

#. If the Sphinx docs are not stored in the ``master`` branch, Read the Docs may not be able to find them, even if the correct branch is set as default on the Git-hosting service (on GitHub, that means Settings => Branches => Default Branch). To ensure that Read the Docs reads from the correct branch, set it at::

      Read the Docs project: Admin => Advanced Settings => Default branch

   Also on the "Advanced Settings" page, it may be useful to set the Python interpreter to the correct version of Python for the project (CPython 3.x).

   On submit, assuming a webhook is found, Read the Docs will build and deploy a new version, using the branch set.

   The build may fail if you make too many attempts to build within a very short time.

   If a build attempt fails, Python or other tracebacks are visible if you click on the attempt in question, on the Builds pages. Currently (20170611) the presence of ``pkg-resource==0.0.0`` in ``requirements.txt`` causes such a failure, so edit it out if you have updated that file from ``pip freeze``.

[end]
