######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


import os
import wfdb
import math
import numpy as np
import dateutil.parser
import logging


import model
from model.data import TimeSeries
from bsml import BSML
from utils import file_uri

from fileformats import BSMLRecording, BSMLSignal



class WFDBRecording(BSMLRecording):
#==================================

  def __init__(self, fname, uri=None, metadata=None):
  #-------------------------------------------------

    wfdb.setgvmode(wfdb.WFDB_HIGHRES)
    ## http: url needs .hea extension??

    #logging.debug('Opening: %s (%s)', fname, uri)
    self._siginfo = wfdb.isigopen(fname)
    if self._siginfo is None: raise IOError("Cannot open header for X '%s'" % fname)
    self._nsignals = self._siginfo.nsig

    wfdbname = wfdb.wfdbfile(None, None)
    recname = wfdbname[:-4] if wfdbname.endswith('.hea') else wfdbname
    if   recname.startswith('http://') or recname.startswith('ftp://'):
      source = wfdbname
    else:
      recname = file_uri(recname)
      source = file_uri(wfdbname)
    if not uri: uri = recname
    ##logging.debug('rec: %s, source: %s', recname, source)

    if metadata is None: metadata = { }
    metadata['format'] = BSML.WFDB
    metadata['source'] = source
    super(WFDBRecording, self).__init__(uri=uri, metadata = metadata)
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
        self.add_signal(WFDBSignal(n, self, metadata =
         { 'label': self._siginfo[n].desc,
           'units': self._siginfo[n].units,
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
    return cls(fname, uri=uri)               ## This is the same as BSML superclass


    """

    A WFDB annotation is an irregularly sampled signal...

    #self._annotators = database_name/ANNOTATORS...
    for ann in self._annotators:
      ainfo = wfdb.WFDB_Anninfo()
      ainfo.name = ann
      ainfo.stat = wfdb.WFDB_READ
      if wfdb.annopen(fname, ainfo, 1) < 0:
        raise IOError("Cannot get annotation '%s' info for '%s'" % (ann, fname))

      annot = wfdb.WFDB_Annotation()
      while wfdb.getann(0, annot.cast()) == 0:

        start = wfdb.timstr(annot.time)  # sinces record start

        wfdb.annstr(annot.anntyp)
        annot.subtyp
        annot.chan
        annot.num
        if annot.aux is not None: aux = annot.aux[1:]
        else:                     aux = ""

        self.add_event(....)
    """

  def close(self):
  #---------------
    wfdb.wfdbquit()

  def _read_frame(self, signo = -1):
  #---------------------------------
    if signo < 0 or signo in self.data_signals:
      v = wfdb.WFDB_SampleArray(self._framesize)
      while wfdb.getframe(v.cast()) == self._nsignals:
        if signo < 0: yield [v[i] for i in xrange(self._framesize) if self._sigpoints[i]]
        else:         yield [v[i] for i in xrange(*self._offsets[n])]


class WFDBSignal(BSMLSignal):
#============================

  MAXPOINTS = 512 #  4096

  def __init__(self, signum, rec, metadata={}):
  #--------------------------------------------
    super(WFDBSignal, self).__init__(str(rec.uri) + '/signal/%d' % signum,  metadata = metadata)
##      metadata = { 'label': edf._edffile.label[signum],
##                   'units': edf._edffile.units[signum],
##                   'transducer': edf._edffile.transducer[signum],
##                   'filter': edf._edffile.prefilter[signum],
##                   'rate': edf._edffile.rate[signum],
##                   'maxFrequency': edf._edffile.rate[signum]/2.0,
##                   'minValue': edf._edffile._physmin[signum],
##                   'maxValue': edf._edffile._physmax[signum],
##                 }
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

    ## Read is of a record's vector/frame...

    ## So check state of rec.vector or rec.frame and reposition record as needs be...


    ## Ideally read frame into 2D np.array and take appropriate slice when
    ## creating TimeSeries...


    if   interval is not None and segment is not None:
      raise Exception("'interval' and 'segment' cannot both be specified")
    if points and duration is not None:
      raise Exception("'points' and 'duration' cannot both be specified")

    if duration: points = int(self.rate*duration + 0.5)


    if points > WFDBSignal.MAXPOINTS or points <= 0:
      points = WFDBSignal.MAXPOINTS

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

    wfdb.tnextvec(self._signum, startpos)
    v = wfdb.WFDB_SampleArray(self._record._nsignals)
    while length > 0:
      if points > length: points = length
      data = (np.array([ v[self._signum]
                           for i in xrange(points)
                             if wfdb.getvec(v.cast()) >= 0 ]) - self._baseline)/self._gain
      if len(data) <= 0: break
      yield TimeSeries(data, rate = self.rate, starttime = float(startpos)/self.rate)
      startpos += len(data)
      length -= len(data)



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
    print ("  Opened %s: source=%s\n   start=%s, duration=%s\n   Nsigs=%s, framerate=%s, framesize=%s"
               % (wf.uri, wf.source, wf.starttime, wf.duration, len(wf), wf._framerate, wf._framesize))

    s = wf.get_signal(index=0)
    printsig(wf, s)

#    for s in wf.signals(): printsig(wf, s)

#    for n, f in enumerate(wf._read_frame()):
#     if n > 0: break
     #print f

    wf.close()

  testrec('mghdb/mgh001')
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
