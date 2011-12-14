"""

At user API level, request a stream (= several channels) at a certain rate.

Each channel has a bandwidth (maxFrequency ??); sample rate must be > 2*maxBandwdith.

If maxBandwidth isn't set for a channel then set it to be half of channel's original
sample rate.

If downsample and new rate will be < 2*maxBW than set maxBW of result = newRate/2 ???
(if 'force' option, else error???)


"""

import fractions


def _gcd(a, b):
#--------------
  while b: a, b = b, a % b
  return a

def _lcm(a, b):
#--------------
  return (a*b)/_gcd(a,b)    #### fractions.gcd(g, n)


def gcd(l):
#==========
  if len(l) == 1: g = l[0]
  else:
    g = _gcd(l[0], l[1])
    for n in l[2:]:
      if g == 1: break
      g = _gcd(g, n)        #### fractions.gcd(g, n)
  return g

def lcm(l):
#==========
  if len(l) == 1: r = l[0]
  else:
    r = _lcm(l[0], l[1])
    for n in l[2:]: r = _lcm(r, n)
  return r

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
