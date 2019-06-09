from neo.Core.Mixins import VerifiableMixin


class InventoryMixin(VerifiableMixin):

    def __init__(self):
        super(InventoryMixin, self).__init__()
        self.InventoryType = None

    def Verify(self):
        pass
