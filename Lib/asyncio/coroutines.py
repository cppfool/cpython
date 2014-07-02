__all__ = ['coroutine',
           'iscoroutinefunction', 'iscoroutine']

import functools
import inspect
import opcode
import os
import sys
import traceback
import types

from . import events
from . import futures
from .log import logger


# Opcode of "yield from" instruction
_YIELD_FROM = opcode.opmap['YIELD_FROM']

# If you set _DEBUG to true, @coroutine will wrap the resulting
# generator objects in a CoroWrapper instance (defined below).  That
# instance will log a message when the generator is never iterated
# over, which may happen when you forget to use "yield from" with a
# coroutine call.  Note that the value of the _DEBUG flag is taken
# when the decorator is used, so to be of any use it must be set
# before you define your coroutines.  A downside of using this feature
# is that tracebacks show entries for the CoroWrapper.__next__ method
# when _DEBUG is true.
_DEBUG = (not sys.flags.ignore_environment
          and bool(os.environ.get('PYTHONASYNCIODEBUG')))

_PY35 = (sys.version_info >= (3, 5))


# Check for CPython issue #21209
def has_yield_from_bug():
    class MyGen:
        def __init__(self):
            self.send_args = None
        def __iter__(self):
            return self
        def __next__(self):
            return 42
        def send(self, *what):
            self.send_args = what
            return None
    def yield_from_gen(gen):
        yield from gen
    value = (1, 2, 3)
    gen = MyGen()
    coro = yield_from_gen(gen)
    next(coro)
    coro.send(value)
    return gen.send_args != (value,)
_YIELD_FROM_BUG = has_yield_from_bug()
del has_yield_from_bug


class CoroWrapper:
    # Wrapper for coroutine in _DEBUG mode.

    def __init__(self, gen, func):
        assert inspect.isgenerator(gen), gen
        self.gen = gen
        self.func = func
        self._source_traceback = traceback.extract_stack(sys._getframe(1))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.gen)

    if _YIELD_FROM_BUG:
        # For for CPython issue #21209: using "yield from" and a custom
        # generator, generator.send(tuple) unpacks the tuple instead of passing
        # the tuple unchanged. Check if the caller is a generator using "yield
        # from" to decide if the parameter should be unpacked or not.
        def send(self, *value):
            frame = sys._getframe()
            caller = frame.f_back
            assert caller.f_lasti >= 0
            if caller.f_code.co_code[caller.f_lasti] != _YIELD_FROM:
                value = value[0]
            return self.gen.send(value)
    else:
        def send(self, value):
            return self.gen.send(value)

    def throw(self, exc):
        return self.gen.throw(exc)

    def close(self):
        return self.gen.close()

    @property
    def gi_frame(self):
        return self.gen.gi_frame

    @property
    def gi_running(self):
        return self.gen.gi_running

    @property
    def gi_code(self):
        return self.gen.gi_code

    def __del__(self):
        # Be careful accessing self.gen.frame -- self.gen might not exist.
        gen = getattr(self, 'gen', None)
        frame = getattr(gen, 'gi_frame', None)
        if frame is not None and frame.f_lasti == -1:
            func = events._format_callback(self.func, ())
            tb = ''.join(traceback.format_list(self._source_traceback))
            message = ('Coroutine %s was never yielded from\n'
                       'Coroutine object created at (most recent call last):\n'
                       '%s'
                       % (func, tb.rstrip()))
            logger.error(message)


def coroutine(func):
    """Decorator to mark coroutines.

    If the coroutine is not yielded from before it is destroyed,
    an error message is logged.
    """
    if inspect.isgeneratorfunction(func):
        coro = func
    else:
        @functools.wraps(func)
        def coro(*args, **kw):
            res = func(*args, **kw)
            if isinstance(res, futures.Future) or inspect.isgenerator(res):
                res = yield from res
            return res

    if not _DEBUG:
        wrapper = coro
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            w = CoroWrapper(coro(*args, **kwds), func)
            if w._source_traceback:
                del w._source_traceback[-1]
            w.__name__ = func.__name__
            if _PY35:
                w.__qualname__ = func.__qualname__
            w.__doc__ = func.__doc__
            return w

    wrapper._is_coroutine = True  # For iscoroutinefunction().
    return wrapper


def iscoroutinefunction(func):
    """Return True if func is a decorated coroutine function."""
    return getattr(func, '_is_coroutine', False)


_COROUTINE_TYPES = (CoroWrapper, types.GeneratorType)

def iscoroutine(obj):
    """Return True if obj is a coroutine object."""
    return isinstance(obj,  _COROUTINE_TYPES)


def _format_coroutine(coro):
    assert iscoroutine(coro)
    if _PY35:
        coro_name = coro.__qualname__
    else:
        coro_name = coro.__name__

    filename = coro.gi_code.co_filename
    if coro.gi_frame is not None:
        lineno = coro.gi_frame.f_lineno
        return '%s() at %s:%s' % (coro_name, filename, lineno)
    else:
        lineno = coro.gi_code.co_firstlineno
        return '%s() done at %s:%s' % (coro_name, filename, lineno)