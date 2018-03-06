
from boa.interop.Neo.Runtime import GetTrigger,CheckWitness
from boa.interop.Neo.Storage import Get,Put,Delete,GetContext
from boa.interop.Neo.TriggerType import Application, Verification

OWNER = b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96'

def Main(operation, addr, value):

    print("Running Sample v4")
    trigger = GetTrigger()
    print(trigger)

    # This determines that the SC is runnning in Verification mode
    # This determines whether the TX will be relayed to the rest of the network
    # The `Verification` portion of SC is *read-only*, so calls to `Storage.Put` will fail.
    # You can, however, use `Storage.Get`
    if trigger == Verification():

        print("Running Verification!")

        # This routine is: if the invoker ( or the Address that signed the contract ) is not OWNER,
        # Then we return False, and the TX will not be relayed to the network
        # Otherwise, we know the owner address signed the TX and return True
        is_owner = CheckWitness(OWNER)

        if is_owner:
            print("Is Owner!")
            return True

        print("Not Owner")

        return False

    elif trigger == Application():

        print("Running Application!")

        if not is_valid_addr(addr):
            print("Not Valid Address")
            return False

        ctx = GetContext()

        if operation == 'add':
            balance = Get(ctx, addr)
            new_balance = balance + value
            Put(ctx, addr, new_balance)
            return new_balance

        elif operation == 'remove':
            balance = Get(ctx, addr)
            Put(ctx, addr, balance - value)
            return balance - value

        elif operation == 'balance':
            return Get(ctx, addr)

    return False


def is_valid_addr(addr):

  if len(addr) == 20:
      return True
  return False
