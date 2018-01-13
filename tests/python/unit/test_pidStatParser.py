
import unittest

from frep import profilers

import testdata


class TestPidStatBegin(unittest.TestCase):

    def setUp(self):
        self.filePath = testdata.filePath('blender_pidstat_dump.txt')
        with open(self.filePath, 'r') as fp:
            self.lines = fp.readlines()
        self.it = iter(self.lines)

    def test_expectFound(self):
        self.assertTrue(profilers.PidStatBegin.find(self.it))

    def test_expectNotFound(self):
        self.it.next()
        self.assertFalse(profilers.PidStatBegin.find(self.it))


class TestPidStatEnd(unittest.TestCase):

    def setUp(self):
        self.filePath = testdata.filePath('blender_pidstat_dump.txt')
        with open(self.filePath, 'r') as fp:
            self.lines = fp.readlines()
        self.it = iter(self.lines)

    def test_expectFound(self):
        self.assertTrue(profilers.PidStatEnd.find(self.lines[-1]))

    def test_expectNotFound(self):
        self.assertFalse(profilers.PidStatEnd.find(self.lines[-2]))


class TestPidStatSample(unittest.TestCase):

    def setUp(self):
        self.filePath = testdata.filePath('blender_pidstat_dump.txt')
        with open(self.filePath, 'r') as fp:
            self.lines = fp.readlines()[4:]
        self.it = iter(self.lines)

    def test_expectHeaderRowAccepted(self):
        line = self.it.next()
        self.assertTrue(profilers.PidStatSample.accept(line))

    def test_expectNumOfParsedRecords(self):
        line = self.it.next()
        columns = list()
        profilers.PidStatSample.accept(line, o_columns=columns)
        records = profilers.PidStatSample().parse(self.it, columns)
        self.assertEqual(20, len(records))

    def test_expectProcessRecordDetails(self):
        line = self.it.next()
        columns = list()
        profilers.PidStatSample.accept(line, o_columns=columns)
        records = profilers.PidStatSample().parse(self.it, columns)
        pRecord = records[0]
        self.assertEqual(1000, pRecord['UID'])
        self.assertAlmostEqual(0.52, pRecord['%MEM'])


class PidStatParser(unittest.TestCase):

    def test_expectParsedStruct(self):
        f = testdata.filePath('blender_pidstat_dump.txt')
        parsed = profilers.PidStatParser(f).parse()
        self.assertTrue(parsed)

    def test_expectNumOfSamples(self):
        f = testdata.filePath('blender_pidstat_dump.txt')
        parsed = profilers.PidStatParser(f).parse()
        self.assertEqual(13, len(parsed))

    def test_expectSampleDetails(self):
        f = testdata.filePath('blender_pidstat_dump.txt')
        parsed = profilers.PidStatParser(f).parse()
        sample = parsed[5]
        self.assertEqual(16368, sample[3]['TID'])

    def test_missingBegin_expectFailed(self):
        f = testdata.filePath('blender_pidstat_dump_missing_begin.txt')
        parsed = profilers.PidStatParser(f).parse()
        self.assertFalse(parsed)

    def test_missingEnd_expectFailed(self):
        f = testdata.filePath('blender_pidstat_dump_missing_end.txt')
        parsed = profilers.PidStatParser(f).parse()
        self.assertFalse(parsed)


if __name__ == '__main__':
    unittest.main()
