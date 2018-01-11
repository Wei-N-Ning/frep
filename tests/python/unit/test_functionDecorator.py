
import unittest

import frep


class P(object):

    def __init__(self, o_dict):
        self.d = o_dict

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.d['called'] = True


class SUT(object):

    def __init__(self):
        self.a = 1

    @frep.deco()
    def meth(self, arg1, arg2=None, *args, **kwargs):
        assert self.a
        return 0xDEAD


@frep.deco()
def sut(arg1, arg2=None, *args, **kwargs):
    return 0xBEEF


class TestFunctionDecorator(unittest.TestCase):

    def test_callFreeFunction_expectOriginalReturnValue(self):
        self.assertEqual(0xBEEF, sut(10))

    def test_getDecoByOriginalFunctionName(self):
        self.assertTrue(frep.getDeco('sut'))

    def test_callMethod_expectOriginalReturnValue(self):
        self.assertEqual(0xDEAD, SUT().meth(10))

    def test_getDecoByOriginalMethodName(self):
        self.assertTrue(frep.getDeco('meth'))

    def test_modifyProfilerAtRuntime(self):
        deco = frep.getDeco('meth')
        d = dict()
        deco.p = P(d)
        SUT().meth(10)
        self.assertTrue(d['called'])

    def test_expectDecoUniqueness(self):
        @frep.deco()
        def foo():
            pass

        @frep.deco()
        def bar():
            pass

        self.assertNotEqual(frep.getDeco('foo'), frep.getDeco('bar'))

