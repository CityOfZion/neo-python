
class Command():

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.prepare(args)

    def prepare(self, args):
        return False

    def execute(self):
        return False
