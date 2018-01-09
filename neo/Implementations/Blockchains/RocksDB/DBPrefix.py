class DBPrefix:

    DATA_Block = b'\x01'
    DATA_Transaction = b'\x02'

    ST_Account = b'\x40'
    ST_Coin = b'\x44'
    ST_SpentCoin = b'\x45'
    ST_Validator = b'\x48'
    ST_Asset = b'\x4c'
    ST_Contract = b'\x50'
    ST_Storage = b'\x70'

    IX_HeaderHashList = b'\x80'

    SYS_CurrentBlock = b'\xc0'
    SYS_CurrentHeader = b'\xc1'
    SYS_Version = b'\xf0'
