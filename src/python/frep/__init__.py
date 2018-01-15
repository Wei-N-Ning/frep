
from augmentation import getDeco


def deco(profiler=None):
    """
    Used as a @decorator

    Args:
        profiler: optional; if not given, a DefaultProfiler is created

    Returns:
        an anonymous decorator object
    """

    import augmentation
    import profilers

    class _d(object):
        """
        Anonymous class

        The only entry points to the instance of this class is the
        public attribute :p:, which is a profiler object that implements
        context manager interface

        One should use frep.getDeco(str) to retrieve this instance
        """

        def __init__(self, p):
            self.p = p

        def __call__(self, f):
            """
            Decorate a function object (a free function or a method);

            Using the DefaultDecorator as the context manager

            Args:
                f (callable): a function object

            Returns:
                callable: anonymous function wrapper
            """
            def _(*args, **kwargs):
                with self.p:
                    return f(*args, **kwargs)
            augmentation.setDeco(f, self)
            return _

    if profiler is None:
        profiler = profilers.DefaultProfiler()

    return _d(profiler)


_patchedFuncs = list()
_patchedMethods = list()


def patch(moduleDotPath, freeFuncs=None, methods=None, profiler=None):
    """
    Use this function to monkey-patch a free-function or method, adding
    a profiler hook to it.

    The free functions and methods are passed in by names,

    moduleDotPath examples:
    'corelib.publish'

    free function examples:
    ['exists', 'send_all', 'publish']

    method examples (using class.method format):
    ['Factory.create', 'Graph.addNode']

    Args:
        moduleDotPath (str):
        freeFuncs (list):
        methods (list):
        profiler (object): a profiler that implements context manager interface

    """
    import profilers

    if profiler is None:
        profiler = profilers.DefaultProfiler()

    def _patchFreeFunc(m, fF):
        fFBackUp = '{}__orig__'.format(fF)
        fOriginal = getattr(m, fF)
        if hasattr(m, fFBackUp):
            return

        def _w(*args, **kwargs):
            with profiler:
                _f = getattr(m, fFBackUp)
                return _f(*args, **kwargs)

        setattr(m, fFBackUp, fOriginal)
        setattr(m, fF, _w)
        _patchedFuncs.append((m, fF, fOriginal, fFBackUp))

    def _patchMethod(m, meth):
        kls, fName = meth.split('.')
        fNameBackUp = '{}__orig__'.format(fName)
        c = getattr(m, kls)
        if hasattr(c, fNameBackUp):
            return

        fOriginal = getattr(c, fName)

        def _w(*args, **kwargs):
            with profiler:
                _f = getattr(c, fNameBackUp)
                return _f(*args, **kwargs)

        setattr(c, fNameBackUp, fOriginal)
        setattr(c, fName, _w)
        _patchedMethods.append((c, fName, fOriginal, fNameBackUp))

    import sys
    m = sys.modules.get(moduleDotPath)
    if m is None:
        m = __import__(moduleDotPath, fromlist=[''])
    if freeFuncs:
        for fF in freeFuncs:
            _patchFreeFunc(m, fF)
    if methods:
        for meth in methods:
            _patchMethod(m, meth)


def unpatchAll():
    """
    Completely restores the patched free functions and methods, leaving no traces
    """
    while _patchedFuncs:
        m, fF, fOriginal, fFBackUp = _patchedFuncs.pop()
        setattr(m, fF, fOriginal)
        delattr(m, fFBackUp)
    while _patchedMethods:
        c, fName, fOriginal, fNameBackUp = _patchedMethods.pop()
        setattr(c, fName, fOriginal)
        delattr(c, fNameBackUp)
