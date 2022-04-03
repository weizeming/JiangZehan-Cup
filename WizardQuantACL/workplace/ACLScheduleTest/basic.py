class Func(object):
    def __init__(self, time, mem, func=None):
        self.time = time
        self.mem = mem
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
