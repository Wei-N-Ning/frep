
import re


def parse(text, ed=None):
    return PerfStatParser(text, ed=ed).parse()


class Begin(object):
    pass


class End(object):
    pass


class PoisonPill(object):
    pass


class Candy(object):
    pass


class PerfStatParser(object):

    def __init__(self, text, ed=None):
        self.text = text
        self._lines = text.split('\n')
        self.ed = ed
        self.candy = None
        self.d = dict()

    def parse(self):
        it = iter(self._lines)
        self._findBegin(it)
        while self._parseLine(it) != Candy:
            pass

        # add a quick sanity check here
        if 'CPU-Utilization' not in self.d:
            raise ValueError('Malformed perf stat output (missing cpu utilization):\n{}'.format(self.text))
        self.d['error'] = self.ed.errorText if self.ed is not None else ''
        self.d['traceback'] = self.ed.tbStrings if self.ed is not None else list()
        return self.d

    def _findBegin(self, it):
        for i in xrange(5):
            try:
                line = it.next()
            except StopIteration, e:
                break
            if re.match('^.*Performance counter stats', line):
                return
        raise ValueError('Malformed perf stat output (missing header):\n{}'.format(self.text))

    def _parseLine(self, it):
        try:
            line = it.next()
        except StopIteration, e:
            raise ValueError('Malformed perf stat output (missing footer):\n{}'.format(self.text))
        r = re.match('^\s+([\d.]+) seconds time elapsed', line)
        if r:
            self._addRecord(r.groups()[0], 'time-elapsed', None)
            return Candy
        r = re.match('^\s+([\d,.]+)\s+(.*)#\s+(.*)$', line)
        if r:
            self._addRecord(*r.groups())

    def _addRecord(self, v, k, d):
        value = float(v.replace(',', ''))
        k = k.strip()
        if k == 'cpu-clock (msec)':
            uPercent = re.match('^([\d.]+).*$', d)
            assert uPercent is not None
            self.d['CPU-Utilization'] = float(uPercent.groups()[0])
            self.d['CPU-Instructions-executed'] = value
        else:
            self.d[k] = value

