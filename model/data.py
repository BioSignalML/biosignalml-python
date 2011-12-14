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
import logging


class DataError(Exception):
#==========================
  pass


class TimeSeries(object):
#========================
  """
  :param np.ndarray data:  the actual data points.
  :param float starttime: the data block's start time [seconds].
  :param float startpos: the data block's starting index position.
  :param float rate:  the data rate of the signal or 0 if sample times are given.
  :param clock: the sample times for an irregularly sampled signal's data points
                or a TimeSeries object that has a clock with this signal's sample
                times.
  :type  clock: np.ndarray or :class:`TimeSeries` or None

  .. note:: We haven't specified how time is represented, apart from assuming that
            time values are in seconds.
  """
  """
  data    np.array
  start   float
  rate    float
  clock   np.array

  __getitem__(self, i)
  time(self, i)

  append(self, data, clock=None)
  extend(self, timeseries)
  """

  ### What are 'starttime' and 'startpos'? Positions on what timeline??
  ### And their relationship to 'rate'? to 'clock' ??


  def __init__(self, data, starttime=None, startpos=None, rate=0, clock=None):
  #---------------------------------------------------------------------------
    if   rate < 0 or rate == 0 and clock is None:
      raise DataError('Time Series timing must be specified')
    elif rate > 0 and clock is not None:
      raise DataError('Time Series cannot have both a rate and an explicit clock')
    elif starttime is None and startpos is None:
      raise DataError('Either start time or position must be given')
    elif rate == 0 and (starttime is None or startpos is None):
      raise DataError('Start time and position must both be given if clock is explicit')
    elif rate > 0 and starttime is not None and startpos is not None and rate*starttime != startpos:
      raise DataError("Start time doesn't match position with given rate")

    if   starttime is None: starttime = startpos/rate   ## What if rate is None
    elif startpos is None: startpos = int(starttime*rate + 0.5) ##  - ditto -
    self.starttime = starttime
    self.startpos = startpos
    self.rate = rate
    self.period = 1.0/self.rate if self.rate else None
    self.clock = clock
    self.data = data
    if rate == 0 and len(data) != self._timesize():
      raise DataError("Length of clock doesn't match data length")
    if len(data):
      ## Check is no longer meaningful with way time() is calculated...
      ## if starttime != self.time(0): raise DataError('Time Series start time mismatch')
      self.endtime = self.time(len(data) - 1)
    else:
      self.endtime = self.starttime
    self.nextstart = self.period*(self.startpos + len(data)) if self.rate else None

  def __len__(self):
  #-----------------
    return len(self.data)
     
  def __str__(self):
  #-----------------
    return ('<Time Series: rate=%s (p=%s), [start, end]=[%s, %s]>'
     % (self.rate, self.period, self.starttime, self.endtime))

  def __getitem__(self, n):
  #------------------------
    return self.data[n]

  def _timesize(self):
  #-------------------
    if   self.rate:                          return len(self)
    elif isinstance(self.clock, TimeSeries): return self.clock._timesize()
    else:                                    return len(self.clock)

  def time(self, n):
  #-----------------
    """
    Get the time of a data point.

    :param int n: the index of the data point (0-based)
    :rtype: float
    """
    if n < 0 or n >= len(self): raise IndexError
    if self.period:             return self.period*(self.startpos + n)
    elif isinstance(self.clock, TimeSeries): return self.clock.time(n)
    else:                                    return self.clock[n]

  def extend(self, next):
  #----------------------
    """
    Extend a TimeSeries with another.

    :param next: the next data block.
    :type  next: :class: TimeSeries
    """
    if   next.starttime <= self.endtime:
      raise DataError('Joined time series must start after current end')
    elif next.rate != self.rate:
      raise DataError('Cannot join time series with a different rates or timing')
    elif next.rate == 0:
      if (isinstance(next.clock, TimeSeries) and not isinstance(self.clock, TimeSeries)
       or not isinstance(next.clock, TimeSeries) and isinstance(self.clock, TimeSeries)):
        raise DataError("Joined time series has different timing")
    elif self.nextstart and next.starttime != self.nextstart:
      raise DataError("Joined time series doesn't follow on")

    self.data = np.concatenate((self.data, next.data))
    if next.rate == 0 and not isinstance(next.clock, TimeSeries):
      self.clock = np.concatenate((self.clock, next.clock))
    self.endtime = next.endtime
    if self.rate: self.nextstart = self.period*(self.startpos + len(data))
