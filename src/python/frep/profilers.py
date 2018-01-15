"""
Common terminology:

profiler:
    - an utility that inspects the runtime characteristics of a subject over a period of time

SUP:
    - subject under profiling; if a Python function: publish() is being profiled, it is a SUP

pid:
    - process id; uniquely identify a Linux process

tid:
    - software thread id; uniquely identify a software thread owned by a process; note that the id of the main thread
    is the same as the id of the owning process

dump:
    - a binary or ascii file that contains raw, unordered information obtained from a system; normally a parser is
    implemented to interpret this information and reformat it in some software- or human-readable fashion.

"""

import os
import re
import shlex
import signal
import subprocess
import tempfile
import time
import traceback


class DefaultProfiler(object):
    """
    All the profilers must write two special tokens to mark the beginning and the end of the profiling data
    in __enter__() and __exit__() respectively;

    The end token must carry a return code and optionally a error message if any;

    If the end token is missing, that means the SUP (subject under profiling) exits unexpectedly;

    """
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    def create(cls):
        return cls()


def _doNothing(*args, **kwargs):
    return dict()


class ExceptionDescriptor(object):

    def __init__(self):
        self.errorText = None
        self.tbStrings = None

    @classmethod
    def create(cls, exc_type, exc_val, exc_tb):
        if exc_type is None or exc_val is None:
            return None
        ed = cls()
        ed.errorText = repr(exc_val)
        ed.tbStrings = traceback.format_tb(exc_tb)
        return ed


def _noExc(*args, **kwargs):
    return None


class ProcessRecord(dict):

    @classmethod
    def parse(cls, columns, values):
        r = cls()
        for k, v in zip(columns, values):
            r[k] = cls.parseOne(k, v)
        return r

    @classmethod
    def parseOne(cls, k, v):
        if k in ('Time', 'UID', 'TGID', 'TID', 'VSZ', 'RSS',
                 'StkSize', 'StkRef', 'iodelay'):
            return int(v)
        if k in ('minflt/s', 'majflt/s', '%MEM', 'kB_rd/s', 'kB_wr/s',
                 'kB_ccwr/s', ):
            return float(v)
        if k in ('Command', ):
            return v
        raise ValueError('Can not parse: k {}, v {}'.format(k, v))


class PidStatBegin(object):

    @classmethod
    def find(cls, it):
        """
        Rolls the iterator to the line next of <pidstat> marker

        For speed reason it only searches for the first 3 lines.

        Args:
            it (Iterable):

        Returns:
            bool
        """

        for i, line in enumerate(it):
            if i >= 3:
                return False
            if re.match('^<pidstat>$', line):
                return True
        return False


class PidStatEnd(object):

    @classmethod
    def find(cls, line):
        return re.match('^<\/pidstat>.*', line) is not None


class PidStatSample(object):

    @classmethod
    def accept(cls, line, o_columns=None):
        """

        Args:
            line:
            o_columns (list): optional output parameter,
                if given the column names are written

        Returns:
            bool:
        """
        columns = re.findall('[!-~]+', line)
        if not (columns and columns[0] == '#'):
            return False
        if o_columns is not None:
            for c in columns[1:]:
                o_columns.append(c)
        return True

    def parse(self, it, columns):
        """
        The state of the iterator must be rolled to the first row of a sample,
        e.g.
            #      Time   UID      TGID       TID  minflt/s  majflt/s
        -->  1515811161  1000     16367         0      0.00      0.00

        Args:
            it (iterable):
            columns (list): a list of column names; the order and length of column names
                are guaranteed to match with those of the parsed values per-row

        Returns:
            list: a list of PidStatRecord, starting from the process record, followed by
                the thread record(s)
        """
        records = list()
        for line in it:
            values = re.findall('[!-~]+', line)
            if not values:
                break
            r = ProcessRecord.parse(columns, values)
            records.append(r)
        return records


class PidStatParser(object):

    POISON_PILL = (0xDEAD, 0xBEEF)
    CANDY = (0xCAFE, 0xBEBE)

    def __init__(self, filePath, ed=None):
        """

        Args:
            filePath (str):
            ed (ExceptionDescriptor):
        """
        self.filePath = filePath
        self.ed = ed

    @classmethod
    def create(cls, filePath, ed=None):
        return cls(filePath, ed=ed).parse()

    def parse(self):
        result = dict()
        samples = list()
        FAILED = None
        with open(self.filePath, 'r') as fp:
            it = fp.xreadlines()
            if not PidStatBegin.find(it):
                return FAILED
            while True:
                s = self.createSample(it)
                if s is self.POISON_PILL:
                    return FAILED
                if s is self.CANDY:
                    break
                if s is None:
                    continue
                samples.append(s)
        result['samples'] = samples
        result['error'] = self.ed.errorText if self.ed is not None else ''
        result['traceback'] = self.ed.tbStrings if self.ed is not None else list()
        return result

    def createSample(self, it):
        try:
            line = it.next()
        except StopIteration, e:
            return self.POISON_PILL
        columns = list()
        if PidStatSample.accept(line, o_columns=columns):
            records = [columns]
            _ = PidStatSample().parse(it, columns)
            if _:
                records.extend(_)
                return records
        if PidStatEnd.find(line):
            return self.CANDY
        return None


class SimpleTimerProfiler(object):

    def __init__(self, excGenerator=None, parser=None, messenger=None):
        self.t = None
        self.excGenerator = excGenerator if excGenerator is not None else _noExc
        self.parser = parser if parser is not None else _doNothing
        self.messenger = messenger if messenger is not None else _doNothing

    @classmethod
    def create(cls, messenger=None):
        return cls(excGenerator=ExceptionDescriptor.create, parser=None, messenger=messenger)

    def __enter__(self):
        self.t = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        ed = self.excGenerator(exc_type, exc_val, exc_tb)
        d = dict(time=time.time() - self.t)
        d['error'] = ed.errorText if ed is not None else ''
        d['traceback'] = ed.tbStrings if ed is not None else list()
        self.messenger(d)


class PerfStatProfiler(object):
    code = \
"""#!/usr/bin/env python
import os
import time
for i in xrange({}):
    if os.path.exists('{}'):
        break
    time.sleep({})

"""
    timeout = 3600  # 3600 seconds
    interval = 0.1  # sleep(0.1)
    numIterations = int(timeout / interval)  # 36000
    filePath = '/tmp/wait_for_exec_{}.py'

    def __init__(self, pid=None, excGenerator=None, parser=None, messenger=None):
        self.pid = pid
        self.excGenerator = excGenerator if excGenerator is not None else _noExc
        self.parser = parser if parser is not None else _doNothing
        self.messenger = messenger if messenger is not None else _doNothing
        self.p = None

    def _writeFile(self):
        filePath = self.filePath.format(self.pid)
        code = self.code.format(self.numIterations, filePath, self.interval)
        with open(filePath, 'w') as fp:
            fp.write(code)
        os.chmod(filePath, 0777)
        return filePath

    def __enter__(self):
        filePath = self._writeFile()
        cmds = shlex.split('perf stat -a -d -t {} {}'.format(self.pid, filePath))
        self.p = subprocess.Popen(cmds, env=dict(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def __exit__(self, exc_type, exc_val, exc_tb):
        filePath = self.filePath.format(self.pid)
        os.remove(filePath)
        while self.p.poll() is None:
            time.sleep(0.05)
        assert self.p.poll() == 0
        print self.p.stdout.read()
        print self.p.stderr.read()


class PidStatProfiler(object):
    """
    Wrapping pidstat

    If the pidstat process returns before __enter__() sends it SIGINT signal, it has reached the MAX DURATION (one
    hour). This is treated as a special exception.

    Attributes:

        DELETE_UPON_COMPLETION (bool):
            whether to delete the pidstat dump file;
            tests can sub-class this profiler and set its value to False in order to inspect the content of the dump

        INTERVAL (int):
            how frequently will the profiler inspect the process; the minimum is 1
            see pidstat -h

        MAX_DURATION (int)
            how long will the profiler keep inspecting the process if caller does not send it SIGINT;
            by default it runs for one hour (3600);
            user can sub-class this profiler and change this value;
            beware that it has directly impact on the size of the dump file

        BEGIN (str)
        END (str)
            mark the start and end of the dump file;
            this provides a simple integrity checkpoint so that the parser can tell whether the subject-under-profiling,
            SUP, exits unexpectedly (i.e. encounters sig-11)

    """
    DELETE_UPON_COMPLETION = True

    INTERVAL = '1'
    MAX_DURATION = '3600'

    BEGIN = '<pidstat>'
    END = '</pidstat>'

    def __init__(self, pid=None, filePath=None, excGenerator=None, parser=None, messenger=None):
        """

        Args:
            pid (int): optional; by default it calls POSIX getpid()
            filePath (str): optional; by default it calls tempfile.mkstemp() to create a temp file that is recycled
            excGenerator (callable): optional; a function that takes (exc_type, exc_val, exc_tb) then produces an
                ExceptionDescriptor object or None
            parser (callable): optional; a function object that takes (a file path, an ExceptionDescriptor) then
                generates a dict
            messenger (callable): optional; a function object that takes the above dict then sends it to somewhere
        """
        self.pid = pid if pid is not None else os.getpid()
        self.filePath = filePath if filePath is not None else tempfile.mkstemp()[-1]
        self.excGenerator = excGenerator if excGenerator is not None else _noExc
        self.parser = parser if parser is not None else _doNothing
        self.messenger = messenger if messenger is not None else _doNothing
        self.p = None
        self.fd = None

    @classmethod
    def create(cls, messenger=None):
        return cls(excGenerator=ExceptionDescriptor.create, parser=PidStatParser.create, messenger=messenger)

    def __enter__(self):
        self.fd = open(self.filePath, 'w')
        self.fd.write('{}\n'.format(self.BEGIN))
        self.fd.flush()
        self.p = subprocess.Popen(['pidstat', '-dtrsh', '-p', str(self.pid), self.INTERVAL, self.MAX_DURATION],
                                  stdout=self.fd,
                                  stderr=subprocess.PIPE)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.p.poll() is not None:
            # one hour of waiting
            pass
        else:
            self.p.send_signal(signal.SIGINT)
        self.p.poll()
        self.fd.flush()
        self.fd.write('\n{}\n'.format(self.END))
        self.fd.close()
        ed = self.excGenerator(exc_type, exc_val, exc_tb)
        self.messenger(self.parser(self.filePath, ed=ed))
        if type(self).DELETE_UPON_COMPLETION:
            os.remove(self.filePath)
