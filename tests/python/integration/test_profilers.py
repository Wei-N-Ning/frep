
import os
import time
import unittest

from frep import profilers
from frep import deco
from frep import getDeco


class PidStatProfiler(profilers.PidStatProfiler):

    DELETE_UPON_COMPLETION = False
    MAX_DURATION = '10'


class TestPidStatProfiler(unittest.TestCase):

    def test_successfulExecution(self):
        @deco(profiler=PidStatProfiler())
        def slowFunction():
            for i in xrange(2):
                time.sleep(0.79)
        slowFunction()
        p = getDeco('slowFunction').p

        self._expectFileCreated(p.filePath)
        self._expectTokenAtBeginning(p.filePath)
        self._expectTokenAtEnd(p.filePath)
        self._expectGuts(p.filePath)

        os.remove(p.filePath)

    def _expectFileCreated(self, filePath):
        self.assertTrue(os.path.isfile(filePath))

    def _expectTokenAtBeginning(self, filePath):
        with open(filePath, 'r') as fp:
            for l in fp.readlines():
                if l.startswith(PidStatProfiler.BEGIN):
                    return
        raise RuntimeError()

    def _expectTokenAtEnd(self, filePath):
        with open(filePath, 'r') as fp:
            lines = fp.readlines()
            for idx in xrange(len(lines) - 1, -1, -1):
                if lines[idx].startswith(PidStatProfiler.END):
                    return
        raise RuntimeError()

    def _expectGuts(self, filePath):
        with open(filePath, 'r') as fp:
            for l in fp.readlines():
                if l.startswith('#'):
                    return
        raise RuntimeError()

    def test_unsuccessfulExecution(self):
        @deco(profiler=PidStatProfiler())
        def canNotFail():
            return [(10 / i, time.sleep(0.73)) for i in xrange(4, -1, -1)]
        self.assertRaises(Exception, canNotFail)
        p = getDeco('canNotFail').p

        self._expectFileCreated(p.filePath)
        self._expectTokenAtBeginning(p.filePath)
        self._expectTokenAtEnd(p.filePath)
        self._expectGuts(p.filePath)

        os.remove(p.filePath)


if __name__ == '__main__':
    unittest.main()
