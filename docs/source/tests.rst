Tests
-----

Run tests with the following command

.. code-block:: sh

    make test


Run style checks with this command

.. code-block:: sh

    make lint


You can run only the ``neo-python`` tests with this command:

.. code-block:: sh

  python -m unittest discover neo


And run only tests from the ``neo-boa`` project like this:

.. code-block:: sh

  python -m unittest discover boa_test



If you are adding tests or altering functionality, it might be faster to only run a single test.  This can be done like this:

.. code-block:: sh

  python -m unittest neo/test_settings.py
