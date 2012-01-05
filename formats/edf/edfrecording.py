#!/usr/local/bin/python
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
import numpy as np

import biosignalml.model as model
from biosignalml.model   import BSML
from biosignalml.formats import BSMLRecording #, BSMLSignal

from edffile import EDF, EDFFile, InvalidSignalId
from edffile import PATIENTFIELDS, RECORDINGFIELDS
from edfutil import EDFScaler, duration_samples
from edfsignal import EDFSignal


MAXBUFFERS = 100   ## Has to allow for short output data records and long signal segments


class EDFRecording(BSMLRecording):
#=================================

  def __init__(self, fname, edffile, uri=None, metadata={}):
  #---------------------------------------------------------
    super(EDFRecording, self).__init__(fname, uri=uri, metadata=metadata)
    self._edffile = edffile


  @classmethod
  def open(cls, fname, uri=None):
  #------------------------------
    edffile = EDFFile.open(fname)
    self = cls(fname, edffile, uri=uri,
      metadata = { 'format': BSML.EDF,   ## EDF+ as well...   #### look at self.edf_type
                   'starttime': edffile.start_datetime,
                   'duration': edffile.duration,
                   'investigation': edffile.patient,
                   'description': edffile.recording,
                 } )
##    'version': edffile.version,    ## Or a comment field ??

    if edffile.edf_type != EDF.EDF:
      for k in PATIENTFIELDS: self.metadata[k] = getattr(edffile, k, None)
      for k in RECORDINGFIELDS: self.metadata[k] = getattr(edffile, k, None)

    for n in edffile.data_signals:      # Add EDFSignal objects
      self.add_signal(EDFSignal(n, self))

    for n, a in enumerate(edffile.annotations()):
      tm = None
      for m, text in enumerate(a.annotations):
        if text:
          if tm is None: tm = self.interval(a.onset, a.duration)
          self.add_event(model.Event(self.uri + '/annotation/tal_%d_%d' % (n, m),
            metadata = {'description': text, 'time': tm}))

    # Now found common errors...
    self.comment = '\n'.join(edffile.errors)
    return self


  def close(self):
  #---------------
    self._edffile.close()



  """

  Creating a new EDF Recording:

  * From scratch:

    @classmethod
    def create_new(cls):

      return self


  * From a model.Recording instance that has Signals

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

  r = RecordBuffers(0.0, [3, 2], [None, EDFScaler(-1, 1)])
  r.put_data(0, -np.ones(3))
  r.put_data(1,  np.ones(4))
  r.put_data(1,  np.ones(2))
  print r.in_use()
  r.put_data(0, -np.ones(6))
  print r.in_use()
  r.put_data(0,  np.ones(3))
  r.put_data(1, -np.ones(4))
  r.put_data(1, -np.ones(2))
  print r.in_use()
  r.put_data(0,  np.ones(6))
  print r.in_use()

