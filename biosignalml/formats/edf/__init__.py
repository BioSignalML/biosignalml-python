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



import os
import logging
import math

import biosignalml
from biosignalml import BSML
from biosignalml.data import DataSegment, UniformTimeSeries
from biosignalml.formats import BSMLSignal, BSMLRecording, MIMETYPES
from biosignalml.model.mapping import PropertyMap
from biosignalml.rdf import XSD
import biosignalml.units as units


from .edffile import PATIENTFIELDS, RECORDINGFIELDS
from .edffile import EDF, EDFFile, InvalidSignalId


__all__ = [ 'EDFSignal', 'EDFRecording' ]


class EDFSignal(BSMLSignal):
#===========================

  attributes = [ 'index' ]

  mapping = { 'index': PropertyMap(BSML.index, XSD.integer) }


  def __init__(self, uri, units=None, **kwds):
  #-------------------------------------------
    BSMLSignal.__init__(self, uri, units, **kwds)

  @classmethod
  def from_recording(cls, recording, signum):
  #------------------------------------------
    edffile = recording._edffile
    self = cls(str(recording.uri) + '/signal/%d' % signum,
               units.get_units_uri(edffile.units[signum]),
               recording  = recording,
               label      = edffile.label[signum],
               transducer = edffile.transducer[signum],
               filter     = edffile.prefilter[signum],
               rate       = edffile.rate[signum],
#               minValue   = edffile._physmin[signum],
#               maxValue   = edffile._physmax[signum],
               index = signum,
               )
    self.initialise()
    return self

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
      segment = (start, start+length)
    #logging.debug('Segment: %s', segment)

    if segment is None:
      startpos = 0
      length = len(self)
    else:
      startpos = max(0, int(math.floor(segment[0])))
      length = min(len(self), int(math.ceil(segment[1]))+1) - startpos
    #logging.debug('Startpos: %d, len: %d', startpos, length)

    while length > 0:
      if maxpoints > length: maxpoints = length
      sigdata = self.recording._edffile.physical_signal(self.index, startpos, maxpoints)
      #logging.debug('READ %d at %d, got %d', points, startpos, sigdata.length)
      if sigdata.length <= 0: break
      yield DataSegment(float(sigdata.startpos)/self.rate, UniformTimeSeries(sigdata.data, self.rate))
      startpos += sigdata.length
      length -= sigdata.length



class EDFRecording(BSMLRecording):
#=================================

  MIMETYPE = MIMETYPES.EDF
  EXTENSIONS = [ 'edf' ]
  SignalClass = EDFSignal

  def __init__(self, uri, dataset=None, **kwds):
  #---------------------------------------------
    BSMLRecording.__init__(self, uri=uri, dataset=dataset, **kwds)
    self._edffile = None
    newfile = kwds.pop('create', False)
    if dataset:
      if newfile: pass  ## Future...
      else:
        self.initialise()
        self._set_attributes()

  def close(self):
  #---------------
    if self._edffile:
      self._edffile.close()

  def initialise(self, **kwds):
  #----------------------------
    if self.dataset is not None and kwds.pop('open_dataset', True):
      fname = str(self.dataset)
      edffile = EDFFile.open(fname)
      if edffile is None:
        raise IOError("Cannot open '%s'", fname)
      self._edffile = edffile
      for s in self.signals():
        EDFSignal.initialise_class(s)

  def _set_attributes(self):
  #-------------------------
    if self._edffile is None: return
    self.set_attributes(starttime = self._edffile.start_datetime,
                        duration = self._edffile.duration,
                        investigation = self._edffile.patient,
                        description = self._edffile.recording,
                        ## EDF+ as well...   #### look at self.edf_type
##                      version = self._edffile.version,    ## Or a comment field ??
                        )
    if self._edffile.edf_type != EDF.EDF:
      for k in PATIENTFIELDS: self.metadata[k] = getattr(self._edffile, k, None)
      for k in RECORDINGFIELDS: self.metadata[k] = getattr(self._edffile, k, None)
    for n in self._edffile.data_signals:      # Add EDFSignal objects
      self.add_signal(EDFSignal.from_recording(self, n))
    for n, a in enumerate(self._edffile.annotations()):
      segment = None
      for m, text in enumerate(a.annotations):
        if text:
          if segment is None:
            segment = self.add_resource(
                        biosignalml.Segment(self.uri + '/time/tal_%d' % n,
                                            source=self,
                                            time=self.interval(a.onset, a.duration)))
          self.add_resource(
            biosignalml.Annotation(self.uri + '/annotation/tal_%d_%d' % (n, m),
                                   about=segment, comment=text))
    # Now found common errors...
    self.comment = '\n'.join(self._edffile.errors)


if __name__ == '__main__':
#=========================

  #import rpdb2; rpdb2.start_embedded_debugger('test')


  fname = '../../../../workspace/testdata/sinewave.edf'
  edf = EDFRecording.open(fname, uri='http://recordings.biosignalml.org/testdata/sinewave')
  if edf is None:
    raise Exception('Missing file: %s' % fname)

  if edf._edffile.errors:   ## Do this automatically ??
    edf.signalset.comment = "Source file had header errors"


  for s in edf.signals():
    print s

  #window = edf.interval(0.0, 1.0)   # 10 second wide window
  ## Hmm, recording.duration could be a RelativeInterval...
  #while window.start < edf.duration:
  #  for e, h in sigs.iteritems():
  #    for d in e.read(window): h.append(d)
  #  window += 1.0

  for e in edf.events():
    print e

  print edf.metadata_as_string()

  edf.close()
