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

from biosignalml.model.data import TimeSeries
from biosignalml.fileformats import BSMLSignal

from edffile import EDF


class EDFSignal(BSMLSignal):
#===========================

  MAXPOINTS = 4096

  def __init__(self, signum, edf):
  #-------------------------------
    super(EDFSignal, self).__init__(str(edf.uri) + '/signal/%d' % signum,
      metadata = { 'label': edf._edffile.label[signum],
                   'units': edf._edffile.units[signum],
                   'transducer': edf._edffile.transducer[signum],
                   'filter': edf._edffile.prefilter[signum],
                   'rate': edf._edffile.rate[signum],
                   'maxFrequency': edf._edffile.rate[signum]/2.0,
                   'minValue': edf._edffile._physmin[signum],
                   'maxValue': edf._edffile._physmax[signum],
                 } )
    self.index = signum
    self._rec_count = edf._edffile.nsamples[signum]

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


  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    """
    :return: A :class:TimeSeries containing signal data covering the interval.
    """

    """
    read interval needs to set offset (in seconds), usually -ve, that first point
    is ahead of requested interval.

    segment read is inclusive...

    read all is segment (0, len(self))

    """

    if   interval is not None and segment is not None:
      raise Exception("'interval' and 'segment' cannot both be specified")
    if points and duration is not None:
      raise Exception("'points' and 'duration' cannot both be specified")

    if duration: points = int(self.rate*duration + 0.5)
    if points > EDFSignal.MAXPOINTS or points <= 0:
      points = EDFSignal.MAXPOINTS

    # We need to be consistent as to what an interval is....
    # Use model.Interval ??
    if interval is not None:
      segment = (self.rate*interval.start, self.rate*(interval.start+interval.duration) - 1)

    if segment is None:
      startpos = 0
      length = len(self)
    else:
      if segment[0] <= segment[1]: seg = segment
      else:                        seg = (segment[1], segment[0])
      startpos = max(0, int(math.floor(seg[0])))
      length = min(len(self), int(math.ceil(seg[1])) - startpos + 1)

    while length > 0:
      if points > length: points = length
      sigdata = self.recording._edffile.physical_signal(self.index, startpos, points)
      if sigdata[1] <= 0: break
      yield TimeSeries(sigdata[2], rate = self.rate, starttime = float(sigdata[0])/self.rate)
      startpos += sigdata[1]
      length -= sigdata[1]
