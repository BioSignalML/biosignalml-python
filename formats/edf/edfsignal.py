######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID: c9e447e on Wed Mar 3 12:53:44 2010 +1300 by dave $
#
######################################################


import os
import logging
import math

from biosignalml.data import DataSegment, UniformTimeSeries
from biosignalml.formats import BSMLSignal
import biosignalml.units as units

from edffile import EDF


class EDFSignal(BSMLSignal):
#===========================

  def __init__(self, signum, edf):
  #-------------------------------
    BSMLSignal.__init__(self,
      str(edf.uri) + '/signal/%d' % signum,
      units.to_UNITS(edf._edffile.units[signum]),
      metadata = { 'label': edf._edffile.label[signum],
                   'transducer': edf._edffile.transducer[signum],
                   'filter': edf._edffile.prefilter[signum],
                   'rate': edf._edffile.rate[signum],
                   'maxFrequency': edf._edffile.rate[signum]/2.0,
                   'minValue': edf._edffile._physmin[signum],
                   'maxValue': edf._edffile._physmax[signum],
                   'index': signum,
                 } )
    self.initialise(edf)


  def initialise(self):
  #--------------------
    self._rec_count = self.recording._edffile.nsamples[self.index]

    ##if edf._edffile.edf_type == EDF.EDF:
    ##  filter = edf._edffile.prefilter[signum]
    ##else:
    ##  filters = edf._edffile.prefilter[signum].split() ## Is there a standard for parameters??
    ##  filter = edf._edffile.prefilter[signum]   ## But have parameters...

    ## self.set_clock(recording.get_clock(edf._edffile.sampleRate(n)))

    ## Aren't scale/offset really attributes of the data stream...
    ##self.scale = edf._edffile.scaling[signum][0]
    ##self.offset = edf._edffile.scaling[signum][1]


  def __len__(self):
  #----------------
    return self._rec_count*self.recording._edffile._datarecs


# how do we create a new EDF Signal?? Attributes are in EDF file when
# opening an existing signal...

# Options:
# * pass all attributes to a create (class) method and set file header
#   from these before calling __init__()
# * Pass all attributes to __init__ and have it set file header.


  def read(self, interval=None, segment=None, maxduration=None, maxpoints=None):
  #-----------------------------------------------------------------------------
    """
    Read data from a Signal.

    :param interval: The portion of the signal to read.
    :type interval: :class:`~biosignaml.time.Interval`
    :param segment: A 2-tuple with start and finishing data indices, with the end
      point not included in the returned range.
    :param maxduration: The maximum duration, in seconds, of a single returned segment.
    :param maxpoints: The maximum length, in samples, of a single returned segment.
    :return: An `iterator` returning :class:`~biosignalml.data.DataSegment` segments
      of the signal data.

    If both ``maxduration`` and ``maxpoints`` are given their minimum value is used.
    """

    if   interval is not None and segment is not None:
      raise Exception("'interval' and 'segment' cannot both be specified")

    if maxduration:
      pts = int(self.rate*maxduration + 0.5)
      if maxpoints: maxpoints = min(maxpoints, pts)
      else: maxpoints = pts
    if maxpoints is None or not (0 < maxpoints <= BSMLSignal.MAXPOINTS):
      maxpoints = BSMLSignal.MAXPOINTS

    # We need to be consistent as to what an interval is....
    # Use model.Interval ??
    if interval is not None:
      #logging.debug('Interval: (%s, %s)', interval.start, interval.duration)
      start = self.rate*interval.start if interval.start else 0
      if interval.duration is not None:
        length = self.rate*interval.duration
        if length == 0: length = 1   #  Always get at least one data point
      else:
        length = len(self)
      segment = (start, length)
    #logging.debug('Segment: %s', segment)

    if segment is None:
      startpos = 0
      length = len(self)
    else:
      startpos = max(0, int(math.floor(segment[0])))
      length = min(len(self)-startpos, int(math.ceil(segment[1])))
      #logging.debug('Startpos: %d, len: %d, pts: %d', startpos, length, points)

    while length > 0:
      if maxpoints > length: maxpoints = length
      sigdata = self.recording._edffile.physical_signal(self.index, startpos, maxpoints)
      #logging.debug('READ %d at %d, got %d', points, startpos, sigdata.length)
      if sigdata.length <= 0: break
      yield DataSegment(float(sigdata.startpos)/self.rate, UniformTimeSeries(sigdata.data, self.rate))
      startpos += sigdata.length
      length -= sigdata.length
