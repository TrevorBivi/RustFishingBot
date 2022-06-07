from threading import Thread

import time as t

def foo(bar):
    print('hello {0}'.format(bar))
    return "foo"

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

twrv = ThreadWithReturnValue(target=foo, args=('world!',))

twrv.start()
t.sleep(4)

print('isalive',twrv.is_alive())

print(twrv.join())   # prints foo
