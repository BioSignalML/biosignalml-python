######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2013  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
######################################################


import random
import numpy as np
import math
import ctypes as C
import logging

__all__ = [ 'RateConverter', 'ConvertError' ]


SINC_BEST_QUALITY   = 0
SINC_MEDIUM_QUALITY = 1
SINC_FASTEST        = 2
ZERO_ORDER_HOLD     = 3
LINEAR              = 4


class _SRC_STATE(C.Structure):
  pass


class _SRC_DATA(C.Structure):
  _fields_ = [ ('data_in',           C.POINTER(C.c_float)),
               ('data_out',          C.POINTER(C.c_float)),
               ('input_frames',      C.c_long),
               ('output_frames',     C.c_long),
               ('input_frames_used', C.c_long),
               ('output_frames_gen', C.c_long),
               ('end_of_input',      C.c_int),
               ('src_ratio',         C.c_double),
             ]

try:
  _srclib = C.CDLL('libsamplerate.dylib')
except OSError:
  try:
    _srclib = C.CDLL('libsamplerate.so')
  except OSError:
    try:
      _srclib = C.CDLL('libsamplerate.dll')
    except OSError:
      raise OSError("Unable to load libsamplerate library")

src_new = _srclib.src_new
src_new.argtypes = [C.c_int, C.c_int, C.POINTER(C.c_int)]
src_new.restype = C.POINTER(_SRC_STATE)

src_strerror = _srclib.src_strerror
src_strerror.argtypes = [C.c_int]
src_strerror.restype = C.c_char_p

src_set_ratio = _srclib.src_set_ratio
src_set_ratio.argtypes = [C.POINTER(_SRC_STATE), C.c_double]

src_process = _srclib.src_process
src_process.argtypes = [C.POINTER(_SRC_STATE), C.POINTER(_SRC_DATA)]
src_process.restype = C.c_int

src_delete = _srclib.src_delete
src_delete.argtypes = [C.POINTER(_SRC_STATE)]


MAX_OUTPUT_FRAMES = 50000       #: For each yielded data block


class ConvertError(Exception):
#============================#
  pass


class RateConverter(object):
#===========================

  def __init__(self, rate, channels=1, maxoutput=MAX_OUTPUT_FRAMES, method=SINC_MEDIUM_QUALITY):
  #---------------------------------------------------------------------------------------------
    error = C.c_int()
    self._converter = src_new(method, channels, C.byref(error))
    if not self._converter: raise ConvertError(src_strerror(error))
    self.rate = float(rate)
    self._channels = channels
    self._maxoutframes = maxoutput

  def __del__(self):
  #-----------------
    if self._converter:
      src_delete(self._converter)

  def convert(self, data, rate=None, finished=False):
  #--------------------------------------------------
    if data is not None:
      self._inshape = data.shape
      inframes = self._inshape[0]
      assert(self._channels == data.size/inframes)
    else:
      data = np.array([0])
      inframes = 0
    input = data.flatten().astype(np.float32)
    assert(input.flags['CONTIGUOUS'])
    inpos = 0
    outframes = 1 # For first iteration, actual value set below 
    while inframes > 0 or finished and outframes > 0:
      data = _SRC_DATA()
      data.data_in = input[inpos:].ctypes.data_as(C.POINTER(C.c_float))
      data.input_frames = inframes
      data.end_of_input = 1 if finished else 0
      if rate is not None: data.src_ratio = self.rate/rate
      else:                data.src_ratio = 1.0
      output = np.zeros(self._channels*self._maxoutframes, dtype=np.float32)
      data.data_out = output.ctypes.data_as(C.POINTER(C.c_float))
      data.output_frames = self._maxoutframes

      error = src_process(self._converter, data)
      if error: raise ConvertError(src_strerror(error))

      inframes -= data.input_frames_used
      inpos += self._channels*data.input_frames_used
      outframes = data.output_frames_gen
      outshape = (outframes,) + self._inshape[1:]
      if outframes > 0:
        yield output[:self._channels*outframes].reshape(outshape)



if __name__ == "__main__":
#========================#

  times = np.linspace(0.0, 2.0*np.pi, 100)
  signal = np.sin(times)

#  print signal

  resampler = RateConverter(2, maxoutput=50)
  #for o in resampler.convert(signal, 1, finished=True):
  g = resampler.convert(signal, 1, finished=True)
  for o in g:
    print len(o)

  del resampler
