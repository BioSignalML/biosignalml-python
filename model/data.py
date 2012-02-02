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

import numpy as np
from collections import namedtuple

import logging


class DataError(Exception):
#==========================
  pass

DataSegment = namedtuple('DataSegment', 'starttime, dataseries')
'''A tuple containg data along with its starting time.'''


class Clock(object):
#===================
  """
  The sample times of a :class:`TimeSeries`.

  :param np.array times: Array of sample times, in seconds.
  """
  def __init__(self, times):
  #-------------------------
    self._times = times

  def __getitem__(self, key):
  #--------------------------
    return self._times[key]

  def __len__(self):
  #-----------------
    return len(self.__times)

  """
  Add times to a clock.

  :param np.array times: Array of sample times, in seconds.
  """
  def extend(self, times):
  #-----------------------
    if self._times[-1] >= times[0]:
      raise DataError('Times must be increasing')
    self._times = np.append(self._times, times)


class UniformClock(Clock):
#=========================
  """
  The sample times of a :class:`UniformTimeSeries`.

  :param float rate: The sample rate, in Hertz.
  """
  def __init__(self, rate):
  #------------------------
    self._rate = float(rate)

  def __getitem__(self, key):
  #--------------------------
    print key, self._rate
    if isinstance(key, slice):
      if key.stop is None: raise TypeError
      return np.arange(key.start if key.start is not None else 0,
                       key.stop, key.step)/self._rate
    elif isinstance(key, int):
      return key/self._rate
    else:
      raise TypeError

  """
  A UniformClock runs forever -- give a length of 0.
  """
  def __len__(self):
  #-----------------
    return 0

  """
  We can not extend a UniformClock.
  """
  def extend(self, times):
  #-----------------------
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
    else:                        self.time = Clock(times)

  def __len__(self):
  #-----------------
    return len(self.data)
     
  def __str__(self):
  #-----------------
    return '<Time Series:\n times=%s\n data=%s>' % (self.times, self.data)

  def __getitem__(self, key):
  #--------------------------
    if isinstance(key, slice): return np.column_stack((self.time[key], self.data[key]))
    elif isinstance(key, int): return (self.time[key], self.data[k])
    else:                      raise TypeError

  @property
  def times(self):
  #---------------
    return self.time[:len(self)]

  @property
  def points(self):
  #----------------
    return np.column_stack((self.times, self.data))

  """
  Extend a time series.

  :param np.array data: Array of data values.
  :param np.array times: Array of sample times, in seconds
    or a :class:`Clock` with times for the entire, extended, time series.
  """
  def extend(self, times, data):
  #-----------------------------
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

  """
  Join two time series together.

  :param TimeSeries series: The time series to add.
  :return: The new :class:`TimeSeries` formed by concatenation.
  """
  def __add__(self, series):
  #-------------------------
    #if isinstance(series, UniformTimeSeries):
    #  return TimeSeries(np.concatenate((self.times, series.times + self.time[-1] + 1.0/series.rate)),
    #                    np.concatenate((self.data, series.data)))
    if self.time[-1] >= series.time[0]:
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
    self.time = UniformClock(self.rate)

  def __str__(self):
  #-----------------
    return '<Time Series, rate=%s: %s>' % (self.rate, self.data)

  """
  Extend a uniform time series.

  :param np.array data: Array of data values.
  """
  def extend(self, data):
  #----------------------
    self.data = np.append(self.data, data)

  """
  Join two uniform time series together.

  :param TimeSeries series: The uniform time series to add.
  :return: The new :class:`UniformTimeSeries` formed by concatenation.
  """
  def __add__(self, series):
  #-------------------------
    if not isinstance(series, UniformTimeSeries):
      raise TypeError('Can only concatenate with another UniformTimeSeries')
    if self.rate != series.rate:
      raise TypeError('Sample rates are different')
    return UniformTimeSeries(np.concatenate((self.data, series.data)), self.rate)


if __name__ == '__main__':
#-------------------------

  import math

  t = np.linspace(0.0, 2.0*math.pi, 101)

  sw = TimeSeries(t, np.sin(t))

  uts = UniformTimeSeries(np.cos(t), 1000)

  np.set_printoptions(threshold=50, edgeitems=5, suppress=True)

  print sw
  print uts
  print uts.points

  sw.extend(uts.times + sw.time[-1] + 1.0/uts.rate, uts.data)

  j = sw

  print j
  print j.points

  print j[95:106]


#  import pylab
#  pylab.plot(j.times, j.data)
#  pylab.show()
