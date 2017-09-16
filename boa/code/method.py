
class Method():

    bp = None

    def __init__(self, code_object):

        self.bp = code_object

        for i, (op, arg) in enumerate(self.bp.code):

            print('[%s] Op: %s -> %s ' % (i, str(op), arg))
