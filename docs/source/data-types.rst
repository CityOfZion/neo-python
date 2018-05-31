------------------------
Data Types in neo-python
------------------------

There are a few data types that are good to be familiar with when using ``neo-python`` or the NEO blockchain in general.  It is useful to have an understanding of these in order to recognize them where they occur in various parts of the system in different formats, and how to work with them. The following section will give a quick overview of each data type and its general usage

Note that these data types are implemented in the ``neocore`` project, but used heavily in ``neo-python``.

KeyPair / Address
-----------------

An address in NEO is actually a public/private key-pair.  When you create a wallet, the password you use is used to create a 32 byte private key that is stored and known only to you.  This key is paired with a 'public' key that is used to identify the address on the network.  The only time a ``private-key`` is used is when signing a transaction.

If you open the ``prompt`` and open a wallet, using the ``wallet`` command will output a few things, but one of them is a list of the ``public keys`` in your wallet, like:

.. code-block:: python3

  "public_keys": [
    {
        "Address": "AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy",
        "Public Key": "036d4de3e05057df18b82718d635795cb67d9c19001e998d76c77b86081be5f160"
    }
  ],


The ``Public Key`` above represents the x and y coordinates on the an `ECDSA <https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm>`_ curve, specifically the *SECP256R1* curve, in a compressed format. We derive the ``Address`` in a series of steps:

- create a ``UInt160`` or ``ScriptHash`` of the public key prepended with ``21`` and finished with ``ac``

  .. code-block:: sh

    >>> from neocore.Cryptography.Crypto import Crypto
    >>> pubkey_hex = '036d4de3e05057df18b82718d635795cb67d9c19001e998d76c77b86081be5f160'
    >>> pubkey_hex_for_addr = '21' + pubkey_hex + 'ac'
    >>> pubkey_hex_for_addr
    '21036d4de3e05057df18b82718d635795cb67d9c19001e998d76c77b86081be5f160ac'
    >>> script_hash = Crypto.ToScriptHash(pubkey_hex_for_addr, unhex=True)
    >>> script_hash
    <neocore.UInt160.UInt160 object at 0x10d33e908>
    >>> script_hash.Data
    bytearray(b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96')

- second, create an address from this script hash:

  .. code-block:: sh

    >>> addr = Crypto.ToAddress(script_hash)
    >>> addr
    'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy'
    >>>

If you are interested in the implementation details of the ``KeyPair``, ``UInt160``, or ``Crypto`` package, have a look at the `neocore repository <https://github.com/CityOfZion/neo-python-core>`_


UInt256
-------

A ``UInt256`` is used to represent a 32 byte hash.  This is normally a hash of a ``Transaction`` object or a ``Block``.  You will normally see it represented as a 64 character string, or a 66 character string with a ``0x`` hex specifier.  Below is a sample of how to interact with a ``UInt256``

.. code-block:: sh

  >>>
  >>> from neocore.UInt256 import UInt256
  >>>
  >>> hash = "0x99e2be05956027b884cbf11cddbf9d2e5a8fb97ab18d5cde44d5ae2d4c980d18"
  >>>
  >>> uint = UInt256.ParseString(hash)
  >>> uint
  <neocore.UInt256.UInt256 object at 0x10cb9b240>
  >>> uint.ToString()
  '99e2be05956027b884cbf11cddbf9d2e5a8fb97ab18d5cde44d5ae2d4c980d18'
  >>> uint.To0xString()
  '0x99e2be05956027b884cbf11cddbf9d2e5a8fb97ab18d5cde44d5ae2d4c980d18'
  >>> uint.Data
  bytearray(b"\x18\r\x98L-\xae\xd5D\xde\\\x8d\xb1z\xb9\x8fZ.\x9d\xbf\xdd\x1c\xf1\xcb\x84\xb8\'`\x95\x05\xbe\xe2\x99")
  >>>
  >>> uint.ToBytes()
  b'99e2be05956027b884cbf11cddbf9d2e5a8fb97ab18d5cde44d5ae2d4c980d18'
  >>>
  >>> data = uint.Data
  >>> data
  bytearray(b"\x18\r\x98L-\xae\xd5D\xde\\\x8d\xb1z\xb9\x8fZ.\x9d\xbf\xdd\x1c\xf1\xcb\x84\xb8\'`\x95\x05\xbe\xe2\x99")
  >>>
  >>> copy = UInt256(data=data)
  >>>
  >>> copy.To0xString()
  '0x99e2be05956027b884cbf11cddbf9d2e5a8fb97ab18d5cde44d5ae2d4c980d18'
  >>>

One thing to note, while we normally see the string, or 0x string version of a UInt256

UInt160
-------

A ``UInt160`` is used to represent a 20 byte hash, and might also be referred to as a ``ScriptHash``.  It is used to represent ``Address`` objects in NEO, whether they are normal addresses or addresses of Smart Contracts on the network. Below is a sample of how to interact with a ``UInt160``

.. code-block:: sh

  >>>
  >>> data = bytearray(b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96')
  >>>
  >>> from neocore.UInt160 import UInt160
  >>>
  >>> new_sh = UInt160(data=data)
  >>> new_sh
  <neocore.UInt160.UInt160 object at 0x10d3460b8>
  >>> new_sh.Data
  bytearray(b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96')
  >>>
  >>> new_sh.To0xString()
  '0x9698b1cac6ce9cbe8517e490778525b929e01903'
  >>>
  >>> sh_again = UInt160.ParseString( new_sh.To0xString() )
  >>> sh_again.Data
  bytearray(b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96')
  >>>
  >>> Crypto.ToAddress( sh_again)
  'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy'
  >>>



Fixed8
------

A ``Fixed8`` is used to represent numbers with 8 decimals in an integer format.  Below is a basic example of using a ``Fixed8``:

.. code-block:: sh

  >>> from neocore.Fixed8 import Fixed8
  >>>
  >>> three = Fixed8.FromDecimal(3)
  >>> three.value
  300000000
  >>> three.ToInt()
  3
  >>> three.ToString()
  '3.0'
  >>>
  >>>
  >>> point5 = Fixed8(50000000)
  >>> point5.ToString()
  '0.5'
  >>>
  >>> point5 + three
  <neocore.Fixed8.Fixed8 object at 0x10cd48ba8>
  >>> threepoint5 = point5 + three
  >>> threepoint5.value
  350000000
  >>>
  >>> threepoint5.ToString()
  '3.5'
  >>>
  >>>
  >>> threepoint5 * 2
  Traceback (most recent call last):
  File "<input>", line 1, in <module>
    threepoint5 * 2
  File "/Users/thomassaunders/Workshop/neo-python/venv/lib/python3.6/site-packages/neocore/Fixed8.py", line 85, in __mul__
    return Fixed8(self.value * other.value)
  AttributeError: 'int' object has no attribute 'value'
  >>>
  >>>


Here are a few thoughts to sum up the above:

- if you want to create a Fixed8 and you have a decimal, the easiest thing to do is to use the ``Fixed8.FromDecimal`` method.
- you can do math on Fixed8 objects, assuming each operand is a ``Fixed8``
- doing math between a ``Fixed8`` and another type of number will raise an error
- you can access the full value of a ``Fixed8`` object by accessing the ``value`` attribute

BigInteger
----------

A ``BigInteger`` is used to store and perform math on arbitrarily sized integers, both negative and positive. The are useful for serializing numbers to bytes and back.  Here is some sample usage of a ``BigInteger``

.. code-block:: sh

  >>> from neocore.BigInteger import BigInteger
  >>>
  >>> bi = BigInteger(10000)
  >>>
  >>> bi.ToByteArray()
  b"\x10'"
  >>>
  >>> bi2 = BigInteger.FromBytes( bi.ToByteArray() )
  >>> bi2
  10000
  >>>
  >>> bi3 = BigInteger(-3)
  >>>
  >>> bi4 = bi2 * bi3
  >>> bi4
  -30000
  >>>
  >>> bi4 += 100000
  >>> bi4
  70000
  >>> bi4.ToByteArray()
  b'p\x11\x01'
  >>>


One thing to note with the ``BigInteger`` implementation is that it differs a bit from ``Fixed8`` in that you can perform math operations between a ``BigInteger`` and a normal integer without problems.


ContractParameterTypes
----------------------

What follows are the ContractParameterTypes that are used in creating and invoking Smart Contracts

.. automodule:: neo.SmartContract.ContractParameterType
    :members:
