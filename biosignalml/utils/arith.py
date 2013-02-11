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

"""

At user API level, request a stream (= several channels) at a certain rate.

Each channel has a bandwidth (maxFrequency ??); sample rate must be > 2*maxBandwdith.

If maxBandwidth isn't set for a channel then set it to be half of channel's original
sample rate.

If downsample and new rate will be < 2*maxBW than set maxBW of result = newRate/2 ???
(if 'force' option, else error???)


"""

import fractions


def lcm(l):
#==========
  return reduce(lambda x, y: (x*y)/fractions.gcd(x,y), l)

def gcd(l):
#==========
  return reduce(fractions.gcd, l)

def ratios(l):
#=============
  m = lcm(l)
  return [m/n for n in l]

"""
ratios([edf.nsamples[n] for n in edf.dataSignals])


Each signal has its own resampler (if ratio != 1)

For each datablock, get each signal block, send to its resampler, so then have
all resampled datablocks. Output single columns of samples...
"""


if __name__ == '__main__':

  l = [ 3, 4, 5 ]

  print 'l =', l, ' gcd(l) =', gcd(l), ' lcm(l) =', lcm(l), ' ratios =', ratios(l)
