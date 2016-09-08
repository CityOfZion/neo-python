# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from AntShares.Wallets.Wallet import Wallet
"""
import urllib
import json
import itertools

ADDR = 'AWHhvbKpw9bfimBTqoYQfx5obE9bUGJ2wi'

URL = 'http://101.200.230.134:8080/api/v1.0/getinfo_with_address/'


def getInputs():
    html = urllib.urlopen("%s%s"%(URL,ADDR))
    content = html.read()
    res = json.loads(content)
    if res.get(u'message', u'error') == u'success':
        data = res.get(u'data', {})
        return sorted(data.iteritems(), key=lambda x:x[1]['value'], reverse=True)
    return res.get(u'message', u'error')

def getChangeAddr():
    return '99d457043351f27a2310cb98f5e6b7bcb61f369f'

def selectInputs(inputs, outputs):
    if len(outputs) > 1 and len(inputs) < 1:
        raise Exception, 'Not Enought Inputs'

    # Count the total amount of change
    coin = itertools.groupby(sorted(inputs, key=lambda x: x[1]['type']), lambda x: x[1]['type'])
    coin_total = dict([(k, sum(int(x[1]['value']) for x in g)) for k,g in coin])

    # Count the pay total
    pays = itertools.groupby(sorted(outputs, key=lambda x: x['Asset']), lambda x: x['Asset'])
    pays_total = dict([(k, sum(int(x['Value']) for x in g)) for k,g in pays])

    # Check whether there is enough change
    for asset, value in pays_total.iteritems():
        if not coin_total.has_key(asset):
            raise Exception, 'Inputs does not contain asset {asset}.'.format(asset=asset)

        if coin_total.get(asset) - value < 0:
            raise Exception, 'Inputs does not have enough asset {asset}, need {amount}.'.format(asset=asset, amount=value)

    # res: used inputs
    # change: change in outpus
    res = []
    change = []

    # Copy the parms
    _inputs  = inputs[:]

    # Find whether have the same value of change
    for asset, value in pays_total.iteritems():
        for _input in _inputs:
            if asset == _input[1]['type'] and value == int(_input[1]['value']):
                # Find the coin
                res.append(_input)
                _inputs.remove(_input)
                break

        else:
            # Find the affordable change

            affordable = sorted([i for i in _inputs if i[1]['type'] == asset and int(i[1]['value']) >= value],
                                key=lambda x: int(x[1]['value']))

            # Use the minimum if exists
            if len(affordable) > 0:
                res.append(affordable[0])
                _inputs.remove(affordable[0])

                # If the amout > value, set the change
                amount = int(affordable[0][1]['value'])
                if amount > value:
                    change.append({'Asset': asset, 'Value': str(amount-value), 'Scripthash': getChangeAddr()})

            else:
                # Calculate the rest of coins
                rest = sorted([i for i in _inputs if i[1]['type'] == asset],
                              key=lambda x: int(x[1]['value']),
                              reverse=True)

                amount = 0
                for _input in rest:
                    amount += int(_input[1]['value'])
                    res.append(_input)
                    _inputs.remove(_input)
                    if amount == value:
                        break
                    elif amount > value:
                        # If the amout > value, set the change
                        change.append({'Asset': asset, 'Value': str(amount-value), 'Scripthash': getChangeAddr()})
                        break

    return res, _inputs, outputs + change


class Wallet(object):
    """docstring for Wallet"""
    def __init__(self):
        super(Wallet, self).__init__()
        self.accounts = {}
        self.contracts = {}
        self.current_height = 0
        self.isrunning = True
        self.isclosed = False

    def getCoinVersion(self):
        return 0x17

    def getWalletHeight(self):
        return self.current_height

    def addContract(self, contract):
        if not self.accounts.has_key(contract.publicKeyHash):
            raise Exception, 'RangeError'

        self.contracts.update({contract.publicKeyHash: contract})

    def toAddress(self, scripthash):
        pass

    def makeTransaction(self, transaction, fee):
        pass

if __name__ == '__main__':
    outputs = [{'Asset': u'AntCoin', 'Value': u'1800', 'Scripthash': '99d457043351f27a2310cb98f5e6b7bcb61f369f'},
               {'Asset': u'AntCoin', 'Value': u'9000', 'Scripthash': '9c17b4ee1441676e36d77a141dd77869d271381d'}]

    inputs, coins, outputs = selectInputs(getInputs(), outputs)
    print 'Inputs:\n', inputs
    print '\nCoins in Wallet:\n', coins
    print '\nOutputs:\n', outputs
