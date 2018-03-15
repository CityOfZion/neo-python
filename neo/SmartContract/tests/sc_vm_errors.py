"""
 Sample smart contract for use in `test_vm_error.py`
"""

from boa.interop.Neo.App import DynamicAppCall


# unfortunately neo-boa doesn't support importing VMFault

def Main(test, args):
    if test == 1:
        # test_invalid_array_index"
        x = args[1]

    elif test == 2:
        # test_negative_array_indexing
        x = args[-1]

    elif test == 3:
        # test_invalid_type_indexing
        x = test[1]

    elif test == 4:
        # test_invalid_appcall
        invalid_contract = b'\x0bA\xfe\xecy\x9e\x12\x8fi\xa2.\xf8\x92T7X@\x93\x9f\xd0'
        DynamicAppCall(invalid_contract, [])
