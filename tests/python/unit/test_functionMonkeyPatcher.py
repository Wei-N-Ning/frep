
import collections
import os
import unittest

import frep


class P(object):

    def __init__(self, o_dict):
        self.d = o_dict

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.d['called'] = True


class TestFunctionMonkeyPatcher(unittest.TestCase):

    def test_patchFreeFunction_expectPatchInEffect(self):
        d = dict()
        p = P(d)
        frep.patch('os.path', freeFuncs=['exists'], profiler=p)
        self.assertFalse(os.path.exists('/doom'))
        self.assertTrue(d['called'])

    def test_unpatchAll_expectFunctionRestored(self):
        d = dict()
        p = P(d)
        frep.patch('os.path', freeFuncs=['exists'], profiler=p)
        frep.unpatchAll()
        self.assertFalse(os.path.exists('/doom'))
        self.assertFalse(d)

    def test_patchMethod_expectPatchInEffect(self):
        d = dict()
        p = P(d)
        frep.patch('collections', methods=['OrderedDict.copy'], profiler=p)
        od = collections.OrderedDict()
        od.copy()
        self.assertTrue(d['called'])

    def test_unpatchAll_expectMethodRestored(self):
        d = dict()
        p = P(d)
        frep.patch('collections', methods=['OrderedDict.copy'], profiler=p)
        frep.unpatchAll()
        od = collections.OrderedDict()
        od.copy()
        self.assertFalse(d)


