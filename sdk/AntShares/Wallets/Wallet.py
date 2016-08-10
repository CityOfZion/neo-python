# -*- coding:utf-8 -*-
"""
Description:
    ECC Curve
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

def selectInputs(inputs, outputs):
    if len(outputs) > 1 and len(inputs) < 1:
        raise Exception, 'Not Enought Inputs'

    # Count the total amount of change
    change = itertools.groupby(sorted(inputs, key=lambda x: x[1]['type']), lambda x: x[1]['type'])
    change_total = dict([(k, sum(int(x[1]['value']) for x in g)) for k,g in changes])
    print changes_total

    # Count the pay total
    pays = itertools.groupby(sorted(outputs, key=lambda x: x['Asset']), lambda x: x['Asset'])
    pays_total = dict([(k, sum(int(x['Value']) for x in g)) for k,g in pays])
    print pays_total

    # Check whether there is enough change
    for asset, value in pays_total.iteritems():
        if not changes_total.has_key(asset):
            raise Exception, 'Inputs does not contain asset {asset}.'.format(asset=asset)

        if changes_total.get(asset) - amount < 0:
            raise Exception, 'Inputs does not have enough asset {asset}, need {amout}.'.format(asset=asset, amout=amount)

        # Find whether have the same value of change
        pass


if __name__ == '__main__':
    outputs = [{'Asset': u'AntCoin', 'Value': u'100', 'Scripthash': '99d457043351f27a2310cb98f5e6b7bcb61f369f'}]
    print selectInputs(getInputs(), outputs)
