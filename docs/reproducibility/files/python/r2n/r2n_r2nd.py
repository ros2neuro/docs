import struct

import numpy as np


class R2ndReader:
    """Sequential little-endian reader of a .r2nd file (the binary decoder model of ROS2neuro): header 'R2NDEC1\\0', version, then
    the fields in the order of the C++ writers. Used by r2n_gaussian_read, r2n_linear_read and r2n_qda_read."""

    def __init__(self, file):
        with open(file, 'rb') as f:
            self.data = f.read()
        self.pos = 0
        if self.data[:7] != b'R2NDEC1':
            raise ValueError('not an .r2nd file')
        self.pos = 8
        self.version = self.u32()

    def u32(self):
        v = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return v

    def u8(self):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def f32(self, n=1):
        v = np.frombuffer(self.data, dtype='<f4', count=n, offset=self.pos).astype(np.float32)
        self.pos += 4 * n
        return v

    def u32s(self, n):
        v = np.frombuffer(self.data, dtype='<u4', count=n, offset=self.pos).astype(np.int64)
        self.pos += 4 * n
        return v

    def string(self):
        n = self.u32()
        s = self.data[self.pos:self.pos + n].decode('utf-8', errors='replace')
        self.pos += n
        return s

    def float_list(self):
        """A float32 vector preceded by its length (the priors)."""
        return self.f32(self.u32())

    def regularization(self):
        """Method (text), then a flag byte and, if it is not 0, the lambda (float32)."""
        self.string()
        if self.u8() != 0:
            self.f32()
