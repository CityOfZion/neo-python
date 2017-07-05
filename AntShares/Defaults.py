
TEST_NODE = "http://localhost:20332/"
TEST_MONGO_HOST = 'localhost'

class Mongo:
    def __init__(self, host=TEST_MONGO_HOST, port=27017, usr=None, pwd=None):
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd

BlockChainDB = Mongo()
