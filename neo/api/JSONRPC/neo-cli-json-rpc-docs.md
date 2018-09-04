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

## `gettxout`

    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "gettxout", "params": ["0ff23561c611ccda65470c9a4a5f1be31f2f4f61b98c75d051e1a72e85a302eb", 1] }'
    {"jsonrpc":"2.0","id":5,"result":{"n":1,"asset":"0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7","value":"25","address":"AHYb3ySrHbhzouZ81ZMnCf8c7zYaoDg64x"}
    
### secondary unspent showing float "value" vs the above int value
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "gettxout", "params": ["9c9f2c430c3cfb805e8c22d0a7778a60ce7792fad52ffe9b34f56de8e2c1d2e6", 1] }'
    {"jsonrpc":"2.0","id":5,"result":{"n":1,"asset":"0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7","value":"2609.997813","address":"ASs7BiaRa9Z2NnJfvf7a4SZ7ciPLiPWefJ"}}
   
### when querying an already spent output
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "gettxout", "params": ["0ff23561c611ccda65470c9a4a5f1be31f2f4f61b98c75d051e1a72e85a302eb", 0] }'
    {"jsonrpc":"2.0","id":5,"result":null}

## `validateaddress`
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": ["AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i"] }'
    {"jsonrpc":"2.0","id":5,"result":{"address":"AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i","isvalid":true}}
    
### with invalid address
    curl -X POST http://seed2.neo.org:20332 -H 'Cication/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": ["152f1muMCNa7goXYhYAQC61hxEgGacmncB"] }'
    {"jsonrpc":"2.0","id":5,"result":{"address":"152f1muMCNa7goXYhYAQC61hxEgGacmncB","isvalid":false}}
    
### with completely invalid argument
    curl -X POST http://seed2.neo.org:20332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 5, "method": "validateaddress", "params": [] }'
    {"jsonrpc":"2.0","id":5,"error":{"code":-2146233086,"message":"Index was out of range. Must be non-negative and less than the size of the collection.\r\nParameter name: index"}}
