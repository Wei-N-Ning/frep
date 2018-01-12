"""
pidstat -dtrs -p $ID
    easier to parse: pidstat -dtrsh -p $ID


"""

import os
import signal
import subprocess
import tempfile


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


def _doNothing(*args, **kwargs):
    return dict()


class ExceptionDescriptor(object):
    pass


def _noExc(*args, **kwargs):
    return None


class PidStatProfiler(object):
    """
    Wrapping pidstat

    If the pidstat process returns before __enter__() sends it SIGINT signal, it has reached the MAX DURATION (one
    hour). This is treated as a special exception.
    """
    DELETE_UPON_COMPLETION = True  # test can sub-class and override this value to False

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
        if type(self).DELETE_UPON_COMPLETION:
            os.remove(self.filePath)
