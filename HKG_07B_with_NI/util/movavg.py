import numpy as np

class MovingAverageFilter:
    def __init__(self, window_size):
        self.window_size = window_size

    def filter(self, x):
        res = []
        for v in x:
            self.buffer[self.i] = v
            m = self.buffer.mean()
            self.i = (self.i + 1) % self.window_size
            res.append(m)
        return res

    def reset(self):
        self.buffer = np.zeros((self.window_size,), dtype=float)
        self.i = 0

