from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
import os
import shutil


class WalletFixtureTestCase(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    @classmethod
    def wallet_1_path(cls):
        return cls.wallets_folder + 'neo-test1-w.wallet'

    @classmethod
    def wallet_1_dest(cls):
        return cls.wallets_folder + 'wallet1.wallet'

    @classmethod
    def wallet_1_pass(cls):
        return '1234567890'

    @classmethod
    def wallet_2_path(cls):
        return cls.wallets_folder + 'neo-test2-w.wallet'

    @classmethod
    def wallet_2_dest(cls):
        return cls.wallets_folder + 'wallet2.wallet'

    @classmethod
    def wallet_2_pass(cls):
        return '1234567890'

    @classmethod
    def wallet_3_path(cls):
        return cls.wallets_folder + 'neo-test3-w.wallet'

    @classmethod
    def wallet_3_dest(cls):
        return cls.wallets_folder + 'wallet3.wallet'

    @classmethod
    def wallet_3_pass(cls):
        return '1234567890'

    @classmethod
    def new_wallet_dest(cls):
        return cls.wallets_folder + 'newwallet.wallet'

    @classmethod
    def new_wallet_pass(cls):
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
