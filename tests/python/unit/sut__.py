
class SUT(object):

    def __init__(self):
        self.a = 1

    def meth(self, arg1, arg2=None, *args, **kwargs):
        assert self.a
        return 0xDEAD


def sut(arg1, arg2=None, *args, **kwargs):
    return 0xBEEF
