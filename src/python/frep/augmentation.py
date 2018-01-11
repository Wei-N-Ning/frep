
_decoRegistrey = dict()


def getDeco(funcName):
    """

    Args:
        funcName (str):

    Returns:
        object: a decorator object
    """
    return _decoRegistrey.get(funcName)


def setDeco(f, w):
    """

    Args:
        f (callable): a function object
        w (object): a decorator object

    """
    try:
        _decoRegistrey[f.__name__] = w
    except AttributeError, e:
        pass
