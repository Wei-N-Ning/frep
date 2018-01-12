
import sys

import unittest


class LazyMonkey(object):

    def __init__(self, moduleDotPath, symbolDotPath):
        self.moduleDotPath = moduleDotPath
        self.symbolDotPath = symbolDotPath

    def patch(self):
        pass

    def unpatch(self):
        pass


class TestLazyMonkey(unittest.TestCase):

    def setUp(self):
        self.reserved = sys.modules.keys()

    def tearDown(self):
        for k in sys.modules.keys():
            if k not in self.reserved:
                sys.modules.pop(k)

    def test_(self):
        lm = LazyMonkey('testdata.product.model.tree', 'AtlasItem.getItemType')
        lm.patch()
        from testdata.product.model import tree
        item = tree.AtlasItem()
        # self.assertEqual('subverted', item.getItemType())


if __name__ == '__main__':
    unittest.main()

