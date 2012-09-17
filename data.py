######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010 - 2011  David Brooks
#
#  $ID$
#
######################################################

__docformat__ = 'restructuredtext'

import logging
import numpy as np


from biosignalml.ontology import BSML
from biosignalml.model.core import AbstractObject
from biosignalml.model.mapping import PropertyMap

from biosignalml.rdf import XSD


class DataError(Exception):
#==========================
  pass


class Clock(AbstractObject):
#===========================
  """
  The sample times of a :class:`TimeSeries`.

  :param np.array times: Array of sample times, in ``resolution`` seconds.
  :param float resolution: The time, in seconds, represented by a time of 1.0. Optional.
  :param float rate: Resolution can be given as the reciprocal of ``rate``. Optional.
  """
  metaclass = BSML.SampleClock

  # Also have 'frequency' ?? and/or 'period' ??
  attributes = [ 'resolution', 'rate' ]

  mapping = { ('resolution', None): PropertyMap(BSML.resolution, XSD.double),
              ('rate',       None): PropertyMap(BSML.rate,       XSD.double) }

  def __init__(self, uri, times, resolution=None, rate=None, **kwds):
  #------------------------------------------------------------------
    if (resolution is not None and rate is not None
     and float(resolution)*float(rate) != 1.0):
      raise DataError("Clock's resolution doesn't match its rate")
    AbstractObject.__init__(self, uri, resolution=resolution, rate=rate, **kwds)
    self._times = times

  def __getitem__(self, key):
  #--------------------------
    """Return the unscaled time at index ``key``."""
    return self._times[key]

  def __len__(self):
  #-----------------
    return len(self._times)

  def scale(self, time):
  #---------------------
    """
    Convert a stored time value to seconds.

    :param float time: Time measured at the clock's resolution.
    :return: The time in seconds.
    """
    if   self.resolution: return self.resolution*float(time)
    elif self.rate:       return float(time)/self.rate
    else:                 return float(time)

  def time(self, pos):
  #-------------------
    """Return the time at index ``pos`` in seconds."""
    return self.scale(self[pos])

  def index(self, t):
  #------------------
    """
    Find the index of a time in the clock.

    :param t: The time to lookup, in seconds.
    :type t: float
    :return: The greatest index such that ``self.time(index) <= t``.
      -1 is returned if ``t`` is before ``self.time(0)``.
    :rtype: int
    """
    i = 0
    j = len(self) - 1
    if time < self.time(0): return -1
    elif time >= self.time(j): return j
    while i <= j:
      m = (i + j)//2
      v = self.time(m)
      print i, j, m, v
      if   v < time: i = m + 1
      elif v > time: j = m - 1
      else: return m
    return m - 1

  def extend(self, times):
  #-----------------------
    """
    Add times to a clock.

    :param np.array times: Array of sample times, in seconds.
    """
    if self._times[-1] >= times[0]:
      raise DataError('Times must be increasing')
    self._times = np.append(self._times, times)


class UniformClock(Clock):
#=========================
  """
  The sample times of a :class:`UniformTimeSeries`.

  :param float rate: The sample rate, in Hertz.
  """
  def __init__(self, uri, rate):
  #-----------------------------
    Clock.__init__(self, uri, None)
    self._rate = float(rate)

  def __getitem__(self, key):
  #--------------------------
    '''
    The time of a single sample, or the array of times of a slice.
    '''
    if isinstance(key, slice):
      if key.stop is None: raise TypeError
      return np.arange(key.start if key.start is not None else 0,
                       key.stop, key.step)/self._rate
    else:
      return key/self._rate

  def __len__(self):
  #-----------------
    """
    A UniformClock runs forever -- give a length of 0.
    """
    return 0

  def index(self, t):
  #------------------
    i = 0
    if t < 0.0: return -1
    else: return int(math.floor(t*self._rate))

  def extend(self, times):
  #-----------------------
    """
    We can not extend a UniformClock.
    """
    raise DataError('Can not extend a UniformClock')


class TimeSeries(object):
#========================
  """
  A series of data values with times.

  :param np.array times: Array of sample times, in seconds or a :class:`Clock` with times.
  :param np.array data: Array of data values.

  append(self, data, clock=None)
  extend(self, timeseries)
  """
  def __init__(self, times, data):
  #-------------------------------
    if len(times) != len(data):
      raise DataError('Number of sample times and data points are different')
    self.data = data
    if isinstance(times, Clock): self.time = times
    else:                        self.time = Clock(None, times)

  def __len__(self):
  #-----------------
    return len(self.data)

  def __str__(self):
  #-----------------
    return '<Time Series: len=%d, times=\n%s\n data=\n%s>' % (len(self), self.times, self.data)

  def __getitem__(self, key):
  #--------------------------
    '''
    A single value as a (time, data) tuple, or a slice as a 2D array of (time, data) points.
    '''
    if isinstance(key, slice): return np.column_stack((self.time[key], self.data[key]))
    elif isinstance(key, int): return (self.time[key], self.data[key])
    else:                      raise TypeError

  @property
  def times(self):
  #---------------
    '''
    The array of sample times.
    '''
    return self.time[:len(self)]

  @property
  def points(self):
  #----------------
    '''
    All the (time, data) points as a 2D array.
    '''
    return np.column_stack((self.times, self.data))

  def extend(self, times, data):
  #-----------------------------
    """
    Extend a time series.

    :param np.array data: Array of data values.
    :param np.array times: Array of sample times, in seconds
      or a :class:`Clock` with times for the entire, extended, time series.
    """
    if self.time[-1] >= times[0]:
      raise DataError('Times must be increasing')
    if isinstance(times, Clock):
      if len(data) != (len(times) - len(self.time)):
        raise DataError('Number of sample times and data points are different')
      if np.sum(self.time, times[len(self.time):]) != 0.0:
        raise DataError('Sample times have changed')
      self.time = times
    else:
      if len(times) != len(data):
        raise DataError('Number of sample times and data points are different')
      self.time.extend(times)
    self.data = np.append(self.data, data)

  def __add__(self, series):
  #-------------------------
    """
    Join two time series together.

    :param TimeSeries series: The time series to add.
    :return: The new :class:`TimeSeries` formed by concatenation.
    """
    #if isinstance(series, UniformTimeSeries):
    #  return TimeSeries(np.concatenate((self.times, series.times + self.time[-1] + 1.0/series.rate)),
    #                    np.concatenate((self.data, series.data)))
    if self.time[-1] >= series.times[0]:  # Using 'times' allows a DataSeries to be added
      raise DataError('Times must be increasing')
    return TimeSeries(np.concatenate((self.times, series.times)),
                      np.concatenate((self.data, series.data)))


class UniformTimeSeries(TimeSeries):
#===================================
  """
  A series of uniformly spaced data values.

  :param np.array data: Array of data values.
  :param float rate: The sample rate, in Hertz.
  :param float period: The sampling period, in seconds, can be specified instead of `rate`,
  """
  def __init__(self, data, rate=None, period=None):
  #------------------------------------------------
    if rate is None and period is None:
      raise DataError('No sampling rate nor period specified')
    elif rate is not None and period is not None:
      raise DataError('Only one of rate or period can be specified')
    self.data = data
    self.rate = rate if rate else 1.0/period
    self.time = UniformClock(None, self.rate)

  def __str__(self):
  #-----------------
    return '<Time Series, len=%d, rate=%s:\n%s>' % (len(self), self.rate, self.data)

  def extend(self, data):
  #----------------------
    """
    Extend a uniform time series.

    :param np.array data: Array of data values.
    """
    self.data = np.append(self.data, data)

  def __add__(self, series):
  #-------------------------
    """
    Join two uniform time series together.

    :param TimeSeries series: The uniform time series to add.
    :return: The new :class:`UniformTimeSeries` formed by concatenation.
    """
    if not isinstance(series, UniformTimeSeries):
      raise TypeError('Can only concatenate with another UniformTimeSeries')
    if self.rate != series.rate:
      raise TypeError('Sample rates are different')
    return UniformTimeSeries(np.concatenate((self.data, series.data)), self.rate)


class DataSegment(object):
#=========================
  '''
  Keep the start time of a time series,

  :param float starttime: The starting time of the time series.
  :param TimeSeries dataseries: A time series.
  '''
  def __init__(self, starttime, dataseries):
  #-----------------------------------------
    self.starttime = starttime
    self.dataseries = dataseries

  def __str__(self):
  #-----------------
    return 'Start: %s, Series: %s' % (self.starttime, self.dataseries)

  def __len__(self):
  #-----------------
    return len(self.data)

  def __getitem__(self, key):
  #--------------------------
    s = self.dataseries[key]
    if isinstance(key, slice): return s + (self.starttime, 0)
    else:                      return (s[0] + self.starttime, s[1])

  @property
  def data(self):
  #--------------
    return self.dataseries.data

  @property
  def times(self):
  #---------------
    return self.dataseries.times + self.starttime

  @property
  def points(self):
  #----------------
    return self.dataseries.points + (self.starttime, 0)


if __name__ == '__main__':
#-------------------------

  import math

  t = np.linspace(0.0, 2.0*math.pi, 101)

  sw = TimeSeries(t, np.sin(t))

  uts = UniformTimeSeries(np.cos(t), 1000)

  np.set_printoptions(threshold=50, edgeitems=5, suppress=True)

  print sw
  print ''
  print uts
  print ''
  print uts.points
  print ''

  dsu = DataSegment(sw.time[-1] + 1.0/uts.rate, uts)
  print dsu
  print ''

#  sw.extend(uts.times + sw.time[-1] + 1.0/uts.rate, uts.data)

  j = sw + dsu

  print j
  print ''
  print j.points
  print ''

  print j[95:106]
  print ''

  ds = DataSegment(100.0, j)
  print ds[95:106]


  c = Clock('http://example.org/clock', [], resolution=0.4)
  print c.resolution
  print c.metadata_as_string()


#  import pylab
#  pylab.plot(j.times, j.data)
#  pylab.show()
