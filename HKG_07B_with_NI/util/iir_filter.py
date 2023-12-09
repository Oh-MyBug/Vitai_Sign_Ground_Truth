from scipy.signal import butter, lfilter, lfilter_zi

class IIRFilter:
    def __init__(self, *args, **kwargs):
        self.b, self.a = butter(*args, **kwargs)
        self.reset()

    def filter(self, x):
        out, self.zi = lfilter(self.b, self.a, x, zi=self.zi)
        return out

    def reset(self):
        self.zi = lfilter_zi(self.b, self.a)

