
import time
import unittest

import frep
from frep import profilers


class TestPerfStatProfiler(unittest.TestCase):

    def setUp(self):
        self.d = None
        p = profilers.PerfStatProfiler(messenger=self.sendMessage)

        @frep.deco(profiler=p)
        def SUP():
            time.sleep(1.5)

        self.SUP = SUP

    def sendMessage(self, d):
        self.d = d

    def test_runSUP_expectProfilingData(self):
        self.SUP()
        self.assertTrue(self.d)
        self.assertTrue(self.d['CPU-Utilization'])


if __name__ == '__main__':
    unittest.main()
