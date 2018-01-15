
import unittest

from frep.parsers import perfStat

import testdata


class TestPerfStatParser(unittest.TestCase):

    def setUp(self):
        self.filePath = testdata.filePath('blender_perfstat_dump.txt')
        with open(self.filePath, 'r') as fp:
            self.text = fp.read()

    def test_emptyText_expectError(self):
        self.assertRaises(ValueError, perfStat.parse, '  ')

    def test_missingHeader_expectError(self):
        self.assertRaises(ValueError, perfStat.parse, '\n\n5373')

    def test_missingFooter_expectError(self):
        text = self.text[:140]
        self.assertRaises(ValueError, perfStat.parse, text)

    def test_expectValidOutput(self):
        d = perfStat.parse(self.text)
        self.assertTrue(d)

    def test_expectCpuUtilizationPercentage(self):
        d = perfStat.parse(self.text)
        _ = d['CPU-Utilization']
        self.assertAlmostEqual(0.003, _[1])

    def test_expectInstructionCount(self):
        d = perfStat.parse(self.text)
        _ = d['instructions']
        self.assertAlmostEqual(1634255, _[0])

    def test_missingCpuUtilizationPercentage_expectError(self):
        text = \
"""
 Performance counter stats for thread id '3650':
            243,926      L1-dcache-load-misses     #   11.74% of all L1-dcache hits
            47,887      LLC-loads                 #    6.068 M/sec                    (34.30%)
     <not counted>      LLC-load-misses                                               (0.00%)

       3.001007753 seconds time elapsed
"""
        self.assertRaises(ValueError, perfStat.parse, text)


if __name__ == '__main__':
    unittest.main()
