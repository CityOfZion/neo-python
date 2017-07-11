
TEST_NODE = "http://seed1.antshares.org:20333/"
TEST_MONGO_HOST = 'localhost'
TEST_ADDRESS = 'AFsRovA3GyLznpAyAYXiv8ZwDswKj1g5A2'

class Mongo:
    def __init__(self, host=TEST_MONGO_HOST, port=27017, usr=None, pwd=None):
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd

BlockChainDB = Mongo()
