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
import numpy as np

import biosignalml
from biosignalml import BSML
from biosignalml.formats import BSMLRecording, MIMETYPES #, BSMLSignal

from edffile import EDF, EDFFile, InvalidSignalId
from edffile import PATIENTFIELDS, RECORDINGFIELDS
from edfutil import EDFScaler, duration_samples
from edfsignal import EDFSignal


MAXBUFFERS = 100   ## Has to allow for short output data records and long signal segments


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


  """

  Creating a new EDF Recording:

  * From scratch:

    @classmethod
    def create_new(cls):

      return self


  * From a biosignalml.Recording instance that has Signals

    @classmethod
    def create_from_recording(cls, recording):




      return self


  @classmethod
  def create(cls, fname, recording, type=EDF.EDF):
  #-----------------------------------------------
    self = cls()
    self._create(open(fname, 'wb'))

    self.signalset = recording

    ## Check recording.get_format == BSML.EDF   ????
    ## Set self._reserved to 'EDF+C' or 'EDF+D' for EDF+ (also BDF ???)

    self.version = 0
    if type == EDF.EDF:
      self.patient = recording.get_investigation()   ## EDF+ fields...
      self.signalset = recording.get_description()   ## EDF+ fields...
      start = recording.get_start_datetime()
      ## Must have 1985 <= start.year <= 2084
      self.startdate = start.strftime('%d.%m.%y')
      self.starttime = start.strftime('%H.%M.%S')

    elif type in [EDF.EDFplusC, EDF.EDFplusD]:     # EDF+
      self._reserved = 'EDF+C' if edf_type == 'EDFplusC' else 'EDF+D'
      ## patient = self.patient.split()
      ## details = self.signalset.split()
      # 'X' value => unknown => don't set attribute

    #### Check for extended EDF+ header fields...
    #### Check for an EDF+ annotation signal....

    self.rate = []
    scaling = []
    self._nsignals = len(recording.signals())
    for s in recording.signals():
      self.rate.append(s.rate)
      self._reservedS.append('')
      self.label.append(s.label)
      self.units.append(s.units)
      self.transducer.append(s.transducer)
      if type == EDF.EDF:
        self.prefilter.append(s.filter)  ## From maxFrequency/bandwidth...
      else:
        pass
        ## filters = self.prefilter[n].split()
        ##
      pmin = s.minValue
      pmax = s.maxValue
      scaler = EDFScaler(pmin, pmax)
      self._physmin.append(pmin)
      self._physmax.append(pmax)
      self._digmin.append(scaler.digital_min)
      self._digmax.append(scaler.digital_max)
      scaling.append(scaler)
      self._signal_uri.append(s.uri)

    (self._drduration, self._nsamples) = duration_samples(self.rate)
    self._recbuffers = RecordBuffers(self, self._drduration, self._nsamples, scaling)
    self.datarecs = 0
    self.writeheader()
    return self



  def output_signal(self, signal):
  #-------------------------------
    try:               n = self._signal_uri.index(signal.uri)
    except ValueError: raise Exception('Unknown output signal: %s' % str(signal.uri))
    if signal.rate and signal.rate != self.rate[n]:
      raise Exception("Signal's rate has changed...")
    elif signal.times is not None:
      raise Exception("EDF doesn't support non-uniform sampling")
    elif signal.start != self._recbuffers.next_start(n, self.rate[n]):
      raise Exception("Discontinuous signals are currently not supported")
    self._recbuffers.put_data(n, signal.data)
    ## And scale if signal.scaling is set...
    # Or have signal.rawdata and data... in TimeSeries ???


  def signal_uris(self):
  #--------------------
    return self._signal_uri

  """

class RecordBuffers(object):
#===========================

  def __init__(self, edffile, duration, sizes, scales):
  #----------------------------------------------------
    self._edffile = edffile
    self._duration = duration
    offsets = [0]
    for i in xrange(1, len(sizes)): offsets.append(offsets[i-1] + sizes[i-1])
    self._recsize = offsets[-1] + sizes[-1]
    self._sigcount = len(sizes)
    self._recordno = 0
    self._buffers = { 0: np.zeros(self._recsize, dtype=np.short) }
    self._usecount = { 0: self._sigcount }
    self._sigbuffer = [ SignalBuffer(0, self._buffers[0], offsets[n], sizes[n], scales[n])
                        for n in xrange(self._sigcount) ]

  def next_buffer(self, recno):
  #----------------------------
    self._usecount[recno] -= 1
    newrecno = recno + 1
    if self._usecount[recno] == 0:
      oldbuf = self._buffers[recno]
      del self._usecount[recno]
      del self._buffers[recno]
      self._edffile.write_record(oldbuf)
      ##print "sending:", oldbuf      ###################
      del oldbuf
    if newrecno in self._buffers:
      newbuf = self._buffers[newrecno]
    else:
      if len(self._buffers) >= MAXBUFFERS: raise Exception('Too many data buffers in use')
      self._recordno += 1
      newbuf = np.zeros(self._recsize, dtype=np.short)
      newrecno = self._recordno
      self._buffers[newrecno] = newbuf
      self._usecount[newrecno] = self._sigcount
    return (newrecno, newbuf)

  def next_start(self, signo, rate):
  #---------------------------------
    return self._duration*self._sigbuffer[signo]._recno + self._sigbuffer[signo]._count/float(rate)

  def put_data(self, signo, data):
  #-------------------------------
    self._sigbuffer[signo].put_data(data, self)

  def in_use(self):
  #----------------
    if len(self._buffers) > 1: return True
    for b in self._sigbuffer:
      if b._count: return True
    return False


class SignalBuffer(object):
#==========================

  def __init__(self, recno, buffer, offset, size, scale):
  #------------------------------------------------------
    self._recno = recno
    self._buffer = buffer
    self._offset = offset
    self._maxsize = size
    self._scale = scale
    self._count = 0

  def __str__(self):
  #-----------------
    return "SignalBuffer: rec=%d, buffer=%s, offset=%d, count=%d" % (self._recno, self._buffer, self._offset, self._count)

  def put_data(self, sigdata, buffers):
  #------------------------------------
    data = self._scale.scale_array(sigdata) if self._scale else sigdata
    datapos = 0
    datalen = len(data)
    while datalen > 0:
      offset = self._offset + self._count
      if (self._count + datalen) <= self._maxsize: length = datalen
      else:                                        length = self._maxsize - self._count
      self._buffer[offset:offset+length] = data[datapos:datapos+length]
      self._count += length
      datapos += length
      datalen -= length
      if self._count == self._maxsize:
        (self._recno, self._buffer) = buffers.next_buffer(self._recno)
        self._count = 0


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

