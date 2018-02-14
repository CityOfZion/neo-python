Installation (Windows)
----------------------

The instructions are written for Windows 7 x64 with MSYS2 environment and Visual Studio 2017. It should probably work for other Windows distributions.


Building LevelDB
================

The easiest way to install leveldb on Windows is using VC++ packaging tool.

::

    git clone https://github.com/Microsoft/vcpkg
    cd vcpkg
    .\bootstrap-vcpkg.bat
    .\vcpkg integrate install
    .\vcpkg install leveldb

If you are using windows x64 you may need to set an environment variable  ``set VCPKG_DEFAULT_TRIPLET=x64-windows`` before installation.

Building plyvel
===============

Activate your Visual Studio build environment e.g.

::

    "e:\Programs\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"

Activate python virtual environment. One of possible ways is using Anaconda.

::

    conda create -n neo python=3.5.4
    activate neo

Build python wheel for plyvel

::

    pip install plyvel==1.0.4

LINK : fatal error LNK1181: cannot open input file 'leveldb.lib'
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Make sure the compiler is able to access .lib and headers of leveldb.
You can try to copy them

from ``vcpkg\installed\x64-windows\include\`` to ``c:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include`` and

from ``vcpkg\installed\x64-windows\lib\libleveldb.lib`` to ``c:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\lib\amd64\leveldb.lib``

error LNK2001: unresolved external symbol __imp_PathFileExistsW
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Find library shlwapi.lib somewhere, probably it already exists on your filesystem. Merge it into leveldb.lib: ``lib.exe /OUT:newleveldb.lib leveldb.lib ShLwApi.Lib`` and replace the original file.

Install neo-python and troubleshooting
======================================

Navigate into the neo-python directory and install the requirements via

::

    pip install -r requirements.txt``

Check the installation ``python prompt.py``

ImportError: No module named 'winrandom'
""""""""""""""""""""""""""""""""""""""""

Navigate into package directory of your python distribution e.g. ``e:\Programs\Anaconda3\envs\neo\Lib\site-packages``.

Change the string ``import winrandom`` to ``from . import winrandom`` in `Crypto\\Random\\OSRNG\\nt.py`

ImportError: No module named 'win32api'
"""""""""""""""""""""""""""""""""""""""

Install module ``pip install pypiwin32``


