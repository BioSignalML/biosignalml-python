######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################


import numpy as np
import math
from ctypes import *
import logging

from biosignalml.model import TimeSeries


SINC_BEST_QUALITY   = 0
SINC_MEDIUM_QUALITY = 1
SINC_FASTEST        = 2
ZERO_ORDER_HOLD     = 3
LINEAR              = 4


class _SRC_STATE(Structure):
  pass


class _SRC_DATA(Structure):
  _fields_ = [ ('data_in',           POINTER(c_float)),
               ('data_out',          POINTER(c_float)),
               ('input_frames',      c_long),
               ('output_frames',     c_long),
               ('input_frames_used', c_long),
               ('output_frames_gen', c_long),
               ('end_of_input',      c_int),
               ('src_ratio',         c_double),
             ]


_srclib = CDLL('libsamplerate.dylib')

src_new = _srclib.src_new
src_new.argtypes = [c_int, c_int, POINTER(c_int)]
src_new.restype = POINTER(_SRC_STATE)

src_strerror = _srclib.src_strerror
src_strerror.argtypes = [c_int]
src_strerror.restype = c_char_p

src_set_ratio = _srclib.src_set_ratio
src_set_ratio.argtypes = [POINTER(_SRC_STATE), c_double]

src_process = _srclib.src_process
src_process.argtypes = [POINTER(_SRC_STATE), POINTER(_SRC_DATA)]
src_process.restype = c_int

src_delete = _srclib.src_delete
src_delete.argtypes = [POINTER(_SRC_STATE)]


class ConvertError(Exception):
#============================#
  pass


class ReSampler(object):
#======================#

  def __init__(self, ratio, channels=1, method=SINC_FASTEST):
  #=========================================================#
    error = c_int()
    self._channels = channels
    self._convertor = src_new(method, channels, byref(error))
    if not self._convertor: raise ConvertError(src_strerror(error))
    src_set_ratio(self._convertor, ratio)
    self._ratio = ratio


  def __del__(self):
  #================#
    src_delete(self._convertor)


  def resample(self, input, output, more, ratio=None):
  #===================================================
    assert(input.dtype == np.float32)
    assert(input.flags['CONTIGUOUS'])
    assert(output.dtype == np.float32)
    assert(output.flags['CONTIGUOUS'])

    if ratio is not None:
      src_set_ratio(self._convertor, ratio)
      self._ratio = ratio
    data = _SRC_DATA()
    data.data_in = input.ctypes.data_as(POINTER(c_float))
    data.input_frames = len(input)/self._channels
    data.end_of_input = 0 if more else 1
    data.src_ratio = self._ratio
    data.data_out = output.ctypes.data_as(POINTER(c_float))
    data.output_frames = len(output)/self._channels

    error = src_process(self._convertor, data)
    if error: raise ConvertError(src_strerror(error))
    return (data.input_frames_used, data.output_frames_gen)


class RateConvertor(ReSampler):
#==============================

  def __init__(self, rate):
  #------------------------
    super(RateConvertor, self).__init__(1.0)
    self.rate = rate
    self._endlen = 0
    self._endstart = 0.0

  def convert(self, ts):
  #---------------------
    ratio = float(self.rate)/float(ts.rate)
    outsize = math.ceil(ratio*len(ts))
    output = np.zeros(outsize, dtype=np.float32)
    (u, g) = self.resample(
               ts.data if ts.data.dtype == np.float32 else ts.data.astype(np.float32),
               output, True, ratio)
    self._endlen += (len(output) - g)
    self._endstart = ts.starttime + float(g)/self.rate
    ## print 'Cvt', len(data), self._endlen, u, g
    return TimeSeries(output if len(output) == g else np.resize(output, g),
                      rate = self.rate, starttime = ts.starttime)


  def finish(self):
  #----------------
    output = np.zeros(self._endlen, dtype=np.float32)
    (u, g) = self.resample(np.zeros(0, dtype=np.float32), output, False)
    return TimeSeries(output, rate = self.rate, starttime = self._endstart)




if __name__ == "__main__":
#========================#

  def resample(input, ratio, output, channels=1, method=SINC_FASTEST):
  #-------------------------------------------------------------------

    resampler = ReSampler(ratio, channels, method)

    BLOCKSIZE = 200
    inpos = 0
    outpos = 0
    inlen = len(input)
    outlen = len(output)

    while inlen > 0:
      if inlen > BLOCKSIZE:
        more = True
        inpoints = BLOCKSIZE
      else:
        more = False
        inpoints = inlen
      (used, generated) = resampler.resample(input[inpos:inpos+inpoints],
                                             output[outpos:outpos+outlen],
                                             more)
      inpos += channels*used
      inlen -= channels*used
      outpos += channels*generated
      outlen -= channels*generated
    return outpos  # Number of output frames


  import pylab as plot
  import math

  R = 0.1  # 100         # ratio
  C = 2           # channels
  P = 1000
  OP = R*P

  sq  = np.zeros(P*C,  dtype=np.float32)
  sq2 = np.zeros(OP*C, dtype=np.float32)
  for i in xrange(P/2, P):
    sq[C*i] = 1.0
#    sq[C*(P-i)-1] = math.cos(8.0*math.pi*i/P)
    sq[C*(P-i)-1] = math.sin(8.0*math.pi*i/P)

  import scipy.signal as sig
#  dq = sig.decimate(sq, int(1/R), n=8)
  rs0 = sig.resample(sq[0:P*C:C], 100)
  rs1 = sig.resample(sq[1:P*C:C], 100)

  o = resample(sq, R, sq2, C) #, LINEAR)

  x = np.linspace(0.0, 1.0, OP)
#  plot.plot(x[0:OP:R], sq[0:P*C:C], label='step in')
#  plot.plot(x[0:OP:R], sq[1:P*C:C], label='cos in')
  plot.plot(x, sq2[0:OP*C:C], label='step out')
  plot.plot(x, sq2[1:OP*C:C], label='cos out')
  plot.plot(x, rs0, label='resample0')
  plot.plot(x, rs1, label='resample1')

  plot.legend()

  plot.show()
