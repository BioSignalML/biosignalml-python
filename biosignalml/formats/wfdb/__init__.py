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
Access PhyiosBank recordings.

.. warning::

   The ``wfdb`` library is not thread safe nor does it support concurrent access to multiple
   recordings from within a thread. The library only allows concurrent access to the same record
   if the recording is repositioned before each read, using a lock to ensure position/read
   operations are atomic.
"""


import os
import wfdb
import math
import threading
import numpy as np
import dateutil.parser
import logging


from biosignalml import BSML
from biosignalml.data import DataSegment, UniformTimeSeries
from biosignalml.utils import file_uri

from biosignalml.formats import BSMLRecording, BSMLSignal, MIMETYPES

__all__ = [ 'WFDBSignal', 'WFDBRecording', 'PHYSIOBANK' ]


PHYSIOBANK = 'http://physionet.org/physiobank/database/'

_WFDBLock      = threading.Lock()
_CurrentRecord = None
_RecordCount   = 0


class WFDBSignal(BSMLSignal):
#============================

  def __init__(self, signum, rec, units, metadata=None):  ## Hmm, URI should be a parameter...
  #-----------------------------------------------------
    BSMLSignal.__init__(self, str(rec.uri) + '/signal/%d' % signum, units, metadata = metadata)
##      metadata = { 'label': edf._edffile.label[signum],
##                   'units': edf._edffile.units[signum],
##                   'transducer': edf._edffile.transducer[signum],
##                   'filter': edf._edffile.prefilter[signum],
##                   'rate': edf._edffile.rate[signum],
##                   'maxFrequency': edf._edffile.rate[signum]/2.0,
##                   'minValue': edf._edffile._physmin[signum],
##                   'maxValue': edf._edffile._physmax[signum],
##                 }
    self.index = signum
    self.initialise(rec)


  def initialise(self):
  #--------------------
    signum = self.index
    self._record = rec
    self._signum = signum
    info = rec._siginfo[signum]
    self._length = info.spf*info.nsamp
    self._gain = info.gain if info.gain != 0 else wfdb.WFDB_DEFGAIN
    self._baseline = info.baseline
    # physical = (ADC - baseline)/gain
    self._samplesperframe = info.spf
    # Total signal samples


  def __len__(self):
  #-----------------
    return self._length


  def read(self, interval=None, segment=None, maxduration=None, maxpoints=None):
  #----------------------------------------------------------------------------
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

    ## Read is of a record's vector/frame...

    ## So check state of rec.vector or rec.frame and reposition record as needs be...

    ## Ideally read frame into 2D np.array and take appropriate slice when
    ## creating TimeSeries...

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
      segment = (self.rate*interval.start, self.rate*(interval.start+interval.duration))
    if segment is None:
      startpos = 0
      length = len(self)
    else:
      if segment[0] <= segment[1]: seg = segment
      else:                        seg = (segment[1], segment[0])
      startpos = max(0, int(math.floor(seg[0])))
      length = min(len(self), int(math.ceil(seg[1])) - startpos)

    # Setup offsets into frame for each signal
    siginfo = self._record._siginfo
    offsets = [ (0, siginfo[0].spf) ]    ## This is record wide data...
    samplesperframe = siginfo[0].spf
    for s in xrange(1, self._record._nsignals):
      offsets.append((samplesperframe, siginfo[s].spf))
      samplesperframe += siginfo[s].spf

    v = wfdb.WFDB_SampleArray(samplesperframe)
    s = self._signum
    while length > 0:
      if maxpoints > length: maxpoints = length
      d = []
      i = maxpoints
      rpos = startpos
      while i > 0:
        global _WFDBLock
        with _WFDBLock:
          wfdb.tnextvec(s, rpos)
          r = wfdb.getframe(v.cast())
        if r <= 0: i = 0
        else:
          for n in xrange(offsets[s][0], offsets[s][0]+offsets[s][1]):
            d.append(v[n])
            i -= 1
            rpos += 1
      data = (np.array(d)-self._baseline)/self._gain
      if len(data) <= 0: break
      yield DataSegment(float(startpos)/self.rate, UniformTimeSeries(data, self.rate))
      startpos += len(data)
      length -= len(data)


class WFDBRecording(BSMLRecording):
#==================================

  MIMETYPE = MIMETYPES.WFDB
  EXTENSIONS = [ 'hea' ]
  SignalClass = WFDBSignal

  def __init__(self, uri, fname=None, **kwds):
  #-------------------------------------------
    BSMLRecording.__init__(self, uri=uri, fname=fname, **kwds)
    self._siginfo = None

  def initialise(self, **kwds):
  #----------------------------
    fname = str(self.dataset)
    global _WFDBLock, _CurrentRecord, _RecordCount
    with _WFDBLock:
      if _CurrentRecord and _CurrentRecord != fname:
        raise IOError("WFDB does not allow concurrent access to different recordings")
      _CurrentRecord = fname
      _RecordCount += 1
    wfdb.setgvmode(wfdb.WFDB_HIGHRES)
    ## http: url needs .hea extension??
    #logging.debug('Opening: %s (%s)', fname, uri)
    if fname.startswith(PHYSIOBANK):
      fname = fname[len(PHYSIOBANK):]
    self._siginfo = wfdb.isigopen(fname)
    if self._siginfo is None:
      raise IOError("Cannot open header for '%s'" % fname)
    self._nsignals = self._siginfo.nsig
    for s in self.signals():
      WFDBSignal.initialise_class(s)

  def _set_attributes(self):
  #-------------------------
    if self._siginfo is None: return
#    wfdbname = wfdb.wfdbfile(None, None)
#    recname = wfdbname[:-4] if wfdbname.endswith('.hea') else wfdbname
#    if   source.startswith('http://') or recname.startswith('ftp://'):
#      source = wfdbname
#    else:
#      recname = file_uri(recname)
#      source = file_uri(wfdbname)
#    if not uri: uri = recname
    ##logging.debug('rec: %s, source: %s', recname, source)

    self._framerate = wfdb.sampfreq(None)/wfdb.getspf()

    start = wfdb.mstimstr(0)
    if start[0] == '[':
      self.starttime = dateutil.parser.parse(start[1:-1], dayfirst=True)
    if self._siginfo[0].nsamp > 0:
      self.duration = self._siginfo[0].nsamp/float(self._framerate)

    ##duration = dateutil.parser.parse(wfdb.mstimstr(wfdb.strtim('e')))
    ##print duration   ## But has date...

    self._framesize = 0
    self.data_signals = [ ]
    self.annotation_signals = [ ]
    self._offsets = [ ]
    offset = 0
    for n in xrange(self._nsignals):
      if self._siginfo[n].desc != 'EDF Annotations':
        self.data_signals.append(n)
        self.add_signal(WFDBSignal(n, self,
         self._siginfo[n].units,
         metadata =
         { 'label': self._siginfo[n].desc,
           'rate': self._framerate*self._siginfo[n].spf,
         } ))
      else:
        self.annotation_signals.append(n)
      self._framesize += self._siginfo[n].spf
      self._offsets.append((offset, self._framesize))
      offset = self._framesize

    self._sigpoints = np.ones(self._framesize, 'bool')
    for n in xrange(self._nsignals):
      if n in self.annotation_signals:
        for i in xrange(*self._offsets[n]): self._sigpoints[i] = False

    #if len(self.annotation_signals) > 0:
      # read all frames, build TAL and add events -- see edffile.py

  ## Some of the above will belong to open() when we have a create()

  @classmethod
  def open(cls, fname, uri=None):
  #------------------------------
    self = cls(uri, fname=fname)
    self.initialise(fname)
    self._set_attributes()
    return self

  def __del__(self):
  #-----------------
    self.close()

  def close(self):
  #---------------
    global _WFDBLock, _CurrentRecord, _RecordCount
    with _WFDBLock:
      _RecordCount -= 1
      if _RecordCount <= 0:
        _CurrentRecord = None
    wfdb.wfdbquit()

  def _read_frame(self, signo = -1):
  #---------------------------------
    if signo < 0 or signo in self.data_signals:
      v = wfdb.WFDB_SampleArray(self._framesize)
      while wfdb.getframe(v.cast()) == self._nsignals:
        if signo < 0: yield [v[i] for i in xrange(self._framesize) if self._sigpoints[i]]
        else:         yield [v[i] for i in xrange(*self._offsets[n])]



if __name__ == '__main__':
#=========================

  ##logging.getLogger().setLevel(logging.DEBUG)

##  import rpdb2; rpdb2.start_embedded_debugger('test')

  def printsig(wf, s):
  #-------------------
    print ("\nSignal %s: (%s) rate=%s\n     gain=%s, base=%s"
                  % (s.uri, s.label, s.rate, s._gain, s._baseline))
    for d in s.read(interval=wf.interval(4.3, 0.1)):
#    for d in s.read(segment=[3, 150]):
      print d
      print d.data


  def testrec(record):
  #-------------------
    print "\nOpening: %s" % record

    wf = WFDBRecording(record)
    print ("  Opened %s: dataset=%s\n   start=%s, duration=%s\n   Nsigs=%s, framerate=%s, framesize=%s"
               % (wf.uri, wf.dataset, wf.starttime, wf.duration, len(wf), wf._framerate, wf._framesize))

    s = wf.signals[0]
    printsig(wf, s)

#    for s in wf.signals(): printsig(wf, s)

#    for n, f in enumerate(wf._read_frame()):
#     if n > 0: break
     #print f

    wf.close()

  testrec('mghdb/mgh002')
  #testrec('100s')
  #testrec('sinewave.edf')
  #testrec('Calib5.edf')
  #testrec('swa49.edf')

"""
>>> import wfdb, sys
>>>
>>> def main(argv):
...     a = wfdb.WFDB_Anninfo()
...     annot = wfdb.WFDB_Annotation()
...     if len(argv) < 3:
...         print "usage:", argv[0], "annotator record"
...         sys.exit(1)
...     a.name = argv[1]
...     a.stat = wfdb.WFDB_READ
...     wfdb.sampfreq(argv[2])
...     if wfdb.annopen(argv[2], a, 1) < 0: sys.exit(2)
...     while wfdb.getann(0, annot) == 0:
...         if annot.aux is not None:
...             aux = annot.aux[1:]
...         else:
...             aux = ""
...         print wfdb.timstr(-annot.time), \
...               "(" + str(annot.time)+ ")", \
...               wfdb.annstr(annot.anntyp), \
...               annot.subtyp, \
...               annot.chan, \
...               annot.num, \
...               aux
...     wfdb.wfdbquit()
...
>>> main(['test', 'atr', 'mitdb/100'])
    0:00 (18) + 0 0 0 (N
    0:00 (77) N 0 0 0
    0:01 (370) N 0 0 0
    0:01 (662) N 0 0 0
    0:02 (946) N 0 0 0
    0:03 (1231) N 0 0 0
    0:04 (1515) N 0 0 0
    0:05 (1809) N 0 0 0
    0:05 (2044) A 0 0 0
    0:06 (2402) N 0 0 0
    0:07 (2706) N 0 0 0
    0:08 (2998) N 0 0 0
    0:09 (3282) N 0 0 0
    0:09 (3560) N 0 0 0
    0:10 (3862) N 0 0 0
    0:11 (4170) N 0 0 0
    0:12 (4466) N 0 0 0
    0:13 (4764) N 0 0 0
    0:14 (5060) N 0 0 0
    0:14 (5346) N 0 0 0
    0:15 (5633) N 0 0 0
"""
