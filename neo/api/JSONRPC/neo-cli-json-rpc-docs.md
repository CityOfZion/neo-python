Documentation for the JSON-RPC implementation

# Links

* http://www.jsonrpc.org/specification
* https://github.com/neo-project/neo/blob/master/neo/Network/RPC/RpcServer.cs
* http://docs.neo.org/en-us/node/api.html

# JSON-RPC API Calls

## `getaccountstate`

### with invalid address

    curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0","method": "getaccountstate","params": ["Axozf8x8GmyLnNv8ikQcPKgRHQTbFi46u2"],"id": 1}' https://seed1.neo.org:20331
    {"jsonrpc":"2.0","id":1,"error":{"code":-2146233033,"message":"One of the identified items was in an invalid format."}

## `getblocksysfee`

    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "getblocksysfee", "params": [13321] }'

    { "jsonrpc": "2.0", "id": 5, "result": "230" }

### with invalid (negative) block height

    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "getblocksysfee", "params": [-1] }'

    {"jsonrpc":"2.0","id":5,"error":{"code":-100,"message":"Invalid Height"}}

## `getrawmempool`

    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "getrawmempool", "params": [] }'
    { "jsonrpc": "2.0", "id": 5, "result": [] }

On MainNet there are actually entries, each of which has this format: `0xde3bc1dead8a89b06787db663b59c4f33efe0afe6b97b1c9c997f2695d7ae0da`

## `getversion`

    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "getversion", "params": [] }'
    { "jsonrpc": "2.0", "id": 5, "result": { "port": 20333, "nonce": 771199013, "useragent": "/NEO:2.6.0/" } }

## `validateaddress`
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": ["AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i"] }'
    {"jsonrpc":"2.0","id":5,"result":{"address":"AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i","isvalid":true}}
    
### with invalid address
    curl -X POST http://seed2.neo.org:20332 -H 'Cication/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": ["152f1muMCNa7goXYhYAQC61hxEgGacmncB"] }'
    {"jsonrpc":"2.0","id":5,"result":{"address":"152f1muMCNa7goXYhYAQC61hxEgGacmncB","isvalid":false}}
    
### with completely invalid argument
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": [] }'
    {"jsonrpc":"2.0","id":5,"error":{"code":-2146233086,"message":"Index was out of range. Must be non-negative and less than the size of the collection.\r\nParameter name: index"}}