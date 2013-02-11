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

'''

* Header info (set by user or metadata parsing...)

* Find datarecord duration based on signal rates

* For each signal:
  * get an EDFScaler (unless data is already int16 (EDF raw))
  * Find nsamples/record


* Output header (with number of datarecs = -1 if unknown).

* As signal data is given to us (via queue, run as a thread ???), buffer into
  data records -- buffer of N datarecs.

* Output a datarec when it is full (i.e. has all signal data).

* TAL records may be short, so "full" means next record would overflow.


'''

import math
import fractions
import numpy as np


# Each signal has its own scaling:

class EDFScaler(object):
#=======================

  def __init__(self, pmin, pmax, dmin=-32768, dmax=32767):
  #-------------------------------------------------------
    '''Given physical min/max, compute scaling so that:

         65534 <  abs(scale*(phys_max - phys_min)) <= 65535
          
        -32768 <=     scale*phys_min + offset      < -32767
         32766 <      scale*phys_max + offset      <= 32767
    '''
    self._scale = float(dmax-dmin)/(pmax - pmin)
    self._offset = float(dmin) - self._scale*pmin
    if   pmin < pmax:
      self._pmin = pmin
      self._pmax = pmax
    elif pmin > pmax:
      self._pmin = pmax
      self._pmax = pmin
    else:
      raise Exception('Physical minimum and maximum must differ')
    self.digital_min = dmin
    self.digital_max = dmax

  def scale(self, x):
  #------------------
    if self._pmin <= x <= self._pmax:
      return int(math.floor(self._scale*float(x) + self._offset + 0.5))
    else:
      raise Exception('Value outside physical range')

  def scale_array(self, a):
  #------------------------
    if self._pmin <= min(a) and max(a) <= self._pmax:
      return np.floor(self._scale*a + self._offset + 0.5).astype(np.short)
    else:
      raise Exception('Values outside physical range')



MAXSAMPLES = 30720      # = 120*256

def lcm(a, b):
#=============
  return a*b/fractions.gcd(a, b)

def gcd_list(l):
#===============
  if len(l) == 1: g = l[0]
  else:
    g = fractions.gcd(l[0], l[1])
    for i in l[2:]:
      if g == 1: break
      g = fractions.gcd(g, i)
  return g

# A list of rates, find data record duration

def duration(rates):
#===================
  d = 1
  for r in rates:
    f = fractions.Fraction.from_float(r).limit_denominator(10000)
    d = lcm(d, f.denominator)
  return d  

def duration_samples(rates):
#===========================
  d = duration(rates)
  s = (d*np.array(rates)).astype(np.int)
  t = np.sum(s)
  if t <= MAXSAMPLES: return (d, s)
  r = int(math.ceil(float(t)/MAXSAMPLES))
  g = gcd_list(s)
  while r <= g and g % r: r+= 1
  if r > g: raise Exception('Too many signals for EDF record')
  return (float(d)/float(r), s/r)

