==============
VisiData v0.94
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

-  Python 3.3+
-  h5py and numpy (if opening .hdf5 files)

**Remember to install the Python3 versions of these packages with e.g.
``pip3``**

Run VisiData
------------

If installed via pip3, ``vd`` should launch without issue.

::

    $ vd [<options>] [<inputs> ...]

If no inputs are given, ``vd`` opens the current directory. Unknown
filetypes are by default viewed with a text browser.

If installed via ``git clone``, first set up some environment variables
(on terminal):

::

    $ export PYTHONPATH=<visidata_dir>:$PYTHONPATH
    $ export PATH=<visidata_dir>/bin:$PATH

License
-------

The innermost core file, ``vd.py``, is licensed under the MIT license.

Other VisiData components, including the main ``vd`` application, addons, and other code in this repository are licensed under GPLv3.

