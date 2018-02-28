from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
import os
import shutil


class WalletFixtureTestCase(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    @classmethod
    def wallet_1_path(cls):
        return './fixtures/testwallet.db3'

    @classmethod
    def wallet_1_dest(cls):
        return './wallet1.db3'

    @classmethod
    def wallet_1_pass(cls):
        return 'testpassword'

    @classmethod
    def wallet_2_path(cls):
        return './fixtures/testwallet2.db3'

    @classmethod
    def wallet_2_dest(cls):
        return './wallet2.db3'

    @classmethod
    def wallet_2_pass(cls):
        return 'testwallet'

    @classmethod
    def wallet_3_path(cls):
        return './fixtures/testwallet3.db3'

    @classmethod
    def wallet_3_dest(cls):
        return './wallet3.db3'

    @classmethod
    def wallet_3_pass(cls):
        return 'testpassword'

    @classmethod
    def new_wallet_dest(cls):
        return './newwallet.db3'

    @classmethod
    def new_wallet_pass(self):
        return 'newwallet'

    @classmethod
    def setUpClass(cls):

        super(WalletFixtureTestCase, cls).setUpClass()

        try:

            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())

            shutil.copyfile(cls.wallet_2_path(), cls.wallet_2_dest())

            shutil.copyfile(cls.wallet_3_path(), cls.wallet_3_dest())

        except Exception as e:
            print("Could not setup WalletFixtureTestCase: %s " % e)

    @classmethod
    def tearDownClass(cls):

        super(WalletFixtureTestCase, cls).tearDownClass()

        try:
            os.remove(cls.wallet_1_dest())
            os.remove(cls.wallet_2_dest())
            if os.path.exists(cls.new_wallet_dest()):
                os.remove(cls.new_wallet_dest())
            if os.path.exists(cls.wallet_3_dest()):
                os.remove(cls.wallet_3_dest())
        except Exception as e:
            print("couldn't remove wallets %s " % e)
