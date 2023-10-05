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

from enum import IntEnum

import numpy as np
import samplerate2 as samplerate

__all__ = [ 'RateConverter', 'ConvertError' ]

#===============================================================================

class ResampleMethod(IntEnum):
  SINC_BEST_QUALITY   = 0
  SINC_MEDIUM_QUALITY = 1
  SINC_FASTEST        = 2
  ZERO_ORDER_HOLD     = 3
  LINEAR              = 4

_samplerate_method = {
  ResampleMethod.SINC_BEST_QUALITY: samplerate.sinc_best,
  ResampleMethod.SINC_MEDIUM_QUALITY: samplerate.sinc_medium,
  ResampleMethod.SINC_FASTEST: samplerate.sinc_fastest,
  ResampleMethod.ZERO_ORDER_HOLD: samplerate.zero_order_hold,
  ResampleMethod.LINEAR: samplerate.linear
}

#===============================================================================

class ConvertError(Exception):
#============================#
  pass

#===============================================================================

class RateConverter(object):
#===========================

  def __init__(self, output_rate, channels=1, method=ResampleMethod.SINC_MEDIUM_QUALITY):
  #--------------------------------------------------------------------------------------
    self.__output_rate = float(output_rate)
    self.__resampler = samplerate.Resampler(_samplerate_method[method], channels)

  def convert(self, data, rate=None, finished=False):
  #--------------------------------------------------
    if data is None:
      data = np.array([0])
    input = data.flatten().astype(np.float32)
    assert(input.flags['CONTIGUOUS'])
    ratio = self.__output_rate/rate if rate is not None else 1.0
    yield self.__resampler.process(input, ratio, finished)

#===============================================================================

if __name__ == "__main__":
#========================#

  times = np.linspace(0.0, 2.0*np.pi, 100)
  signal = np.sin(times)

#  print signal

  resampler = RateConverter(2)
  #for o in resampler.convert(signal, 1, finished=True):
  g = resampler.convert(signal, 1, finished=True)
  for o in g:
    print(len(o))

  del resampler

#===============================================================================
