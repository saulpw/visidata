==============
VisiData v0.96
==============

A terminal interface for exploring and arranging tabular data

Usable via any shell which has Python3 installed.

.. image:: img/birdsdiet_bymass.gif
   :target: https://github.com/saulpw/visidata/blob/develop/docs/tours.rst

Getting Started
===============

Install VisiData
----------------

from pypi (``stable`` branch)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ pip3 install visidata

or clone from git
~~~~~~~~~~~~~~~~~

::

    $ git clone http://github.com/saulpw/visidata.git
    $ cd visidata
    $ pip install -r requirements.txt
    $ python setup.py install

Dependencies
~~~~~~~~~~~~

-  Python 3.4+
-  h5py and numpy (if opening .hdf5 files)

**Remember to install the Python3 versions of these packages with e.g.
``pip3``**

Run VisiData
------------

If installed via pip3, ``vd`` should launch without issue.

::

    $ vd [<options>] <input> ...
    $ <command> | vd
    $ vd [<options>] --play <script.vd> [--<format-field>=<value> ...]
    $ vd [<options>] --play - [--<format-field>=<value> ...] < <script.vd>
    $ vd [<options>] < <input>

If no inputs are given, ``vd`` opens the current directory. Unknown
filetypes are by default viewed with a text browser.

If installed via ``git clone``, first set up some environment variables
(on terminal):

::

    $ export PYTHONPATH=<visidata_dir>:$PYTHONPATH
    $ export PATH=<visidata_dir>/bin:$PATH

License
-------

The innermost core file, ``vdtui.py``, is a single-file stand-alone library that provides a solid framwork for building text user interface apps. It is distributed under the MIT free software license, and freely available for use in other projects. 

Other VisiData components, including the main ``vd`` application, addons, and other code in this repository are licensed under GPLv3.

