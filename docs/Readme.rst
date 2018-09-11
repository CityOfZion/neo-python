Contributing
============

Contributions are always welcome!

Guidelines
----------
When contributing please note the following:

1.  NEO-Python Docs use the sphinx module to build https://neo-python.readthedocs.io/en/latest/. So, make sure every docucment you add uses reStructuredText (e.g. <yourfile>.rst).

2.  After creating your document, be sure to update the ``toctree`` in index.rst. **Failing to do so will result in your document missing from the readthedocs website.**

3.  Before submitting a pull request to add your new document, run ``make docs`` to verify your build is successful and includes no warnings. You will need to install the sphinx module and rtd theme:

::

    pip install sphinx
    pip install sphinx_rtd_theme
