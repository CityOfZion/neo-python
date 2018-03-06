Installation (Windows)
----------------------

The instructions are written for Windows 7 x64 with MSYS2 environment and Visual Studio 2017. It should probably work for other Windows distributions.
Another option is to setup a Linux Subsystem with Ubuntu (see also `here <https://medium.com/@gubanotorious/installing-and-running-neo-python-on-windows-10-284fb518b213>`_ for more infos and a guide).

Building LevelDB
================

The easiest way to install leveldb on Windows is using VC++ packaging tool. If you have windows x64 you may need to set an environment variable  ``set VCPKG_DEFAULT_TRIPLET=x64-windows`` before installation.

::

    git clone https://github.com/Microsoft/vcpkg
    cd vcpkg
    .\bootstrap-vcpkg.bat
    .\vcpkg integrate install
    .\vcpkg install leveldb


Installing python dependencies
==============================

Install `Anaconda package manager <https://www.anaconda.com/download/>`_. Activate python virtual environment.

::

    conda create -n neo python=3.6.4
    activate neo

*(Optional)* Activate your Visual Studio build environment e.g.

::

    "e:\Program Files\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"

Building plyvel (1.0.4)
"""""""""""""""""""""""

Make sure the compiler is able to access .lib and headers of leveldb. Copy them to your destination of MSVS build tools:

from ``vcpkg\installed\x64-windows\include\`` to ``e:\Program Files\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC\14.12.25827\include`` and

from ``vcpkg\installed\x64-windows\lib\libleveldb.lib`` to ``e:\Program Files\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC\14.12.25827\lib\x64\leveldb.lib``

After that, clone the repository, move to the required version, install cython, build python extensions from c++ files and finally install plyvel.

::

    git clone https://github.com/wbolster/plyvel
    cd plyvel
    git checkout e3887a5fae5d7b8414eac4c185c1e3b0cebbdba8
    pip install cython
    cython --cplus --fast-fail --annotate plyvel/_plyvel.pyx
    python setup.py build_ext --inplace --force
    python setup.py install

Building peewee (2.10.2)
""""""""""""""""""""""""

::

    git clone https://github.com/coleifer/peewee
    cd peewee
    git checkout 761f9144a0e17381147a81658019cffe14c118ca
    python setup.py install

Building mmh3 (2.5.1)
"""""""""""""""""""""

::

    git clone https://github.com/hajimes/mmh3
    cd mmh3
    git checkout a73b373858dedfdb6d362f5ca985ae1bb6bc2161
    python setup.py install


Installing dependencies from Anaconda
"""""""""""""""""""""""""""""""""""""

Some of the dependencies could not be installed from pip in a correct way, but Anaconda works well.

::

    conda install twisted==17.9.0
    conda install pycrypto==2.6.1


Install neo-python
==================

Navigate into the neo-python directory and install other dependencies via

::

    pip install -r requirements.txt

Check the installation ``python prompt.py``


Troubleshooting
===============

Probably you could encounter some issues if you haven't followed the guide strictly. Some solutions are listed here.

LINK : fatal error LNK1181: cannot open input file 'leveldb.lib'
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Make sure the compiler is able to access .lib and headers of leveldb.

error LNK2001: unresolved external symbol __imp_PathFileExistsW
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Find library shlwapi.lib somewhere, probably it already exists on your filesystem. Merge it into leveldb.lib: ``lib.exe /OUT:newleveldb.lib leveldb.lib ShLwApi.Lib`` and replace the original file.

ImportError: No module named 'winrandom'
""""""""""""""""""""""""""""""""""""""""

Navigate into package directory of your python distribution e.g. ``e:\Programs\Anaconda3\envs\neo\Lib\site-packages``.

Change the string ``import winrandom`` to ``from . import winrandom`` in `Crypto\\Random\\OSRNG\\nt.py`

ImportError: No module named 'win32api'
"""""""""""""""""""""""""""""""""""""""

Install module ``pip install pypiwin32``


