
import time

from frep import deco
from frep import profilers


def slowFunction():
    for i in xrange(100):
        if i:
            time.sleep(0.012)


@deco(profiler=profilers.PidStatProfiler())
def withProfiler():
    return slowFunction()


def withoutProfiler():
    return slowFunction()


# s = time.time()
# withoutProfiler()
# print time.time() - s  # 1.1942448616


# s = time.time()
# withProfiler()
# print time.time() - s  # 1.19571709633
