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
from datetime import datetime

from biosignalml import BSML
from biosignalml.formats import BSMLRecording, BSMLSignal

from sdffile import ControlFile, DataFile, EventFile


class SDFSignal(BSMLSignal):
#===========================

  def __init__(self, uri, fname, label):
  #-------------------------------------
    super(SDFSignal, self).__init__(uri)
    self.source = 'file://' + os.path.abspath(fname)
    self._datafile = DataFile(fname)
    filelabel = getattr(self._datafile, 'label', None)
    if   not label and not filelabel:
      raise Exception("Signal '%s' has no label" % fname)
    elif label and filelabel and label != filelabel:
      raise Exception("Signal '%s' labels don't agree" % fname)
    elif label: self.label = label
    else:       self.label = filelabel
    self.units = getattr(self._datafile, 'dimension', None)
    self.rate = getattr(self._datafile, 'samplingrate', None)

  def close(self):
  #---------------
    self._datafile.close()

#Recording -standardlabel FZ/A2

#Data -digitalminimum -100
#Data -digitalmaximum 100
#Data -slope -0.500000
#Data -offset 0.000000


class SDFEvent(biosignalml.Event):
#===========================

  def __init__(self, uri, fname, label):
  #-------------------------------------
    super(SDFEvent, self).__init__(uri)
    self.source = 'file://' + os.path.abspath(fname)
    self._eventfile = EventFile(fname)

  def close(self):
  #---------------
    self._eventfile.close()


class SDFRecording(BSMLRecording):
#=================================

  @staticmethod
  def normalise_name(filepath):
  #----------------------------
    path, name = os.path.split(os.path.abspath(os.path.expanduser(filepath)))
    if name == 'control.txt': return filepath
    fileid = os.path.splitext(name)[0]
    if fileid == os.path.split(path)[1]: return os.path.join(path, 'control.txt')
    else:                                return os.path.join(path, fileid, 'control.txt')

  def __init__(self, fname, **kwds):
  #---------------------------------
    super(SDFRecording, self).__init__(fname, **kwds) 
    self.format = BSML.SDF
    try:
      self._control = ControlFile(fname)
      fpath = os.path.split(os.path.abspath(fname))[0] + '/'
    except IOError:
      fpath = os.path.abspath(fname) + '/'
      try:
        self._control = ControlFile(fpath + 'control.txt')
      except IOError:
        raise Exception('Cannot open control file')
    self.source = 'file://' + os.path.abspath(self._control._file.name)
    self.description = self._control.recording.get('format')

    #print self._control.recording
    if self._control.recording.get('date'):
      if self._control.recording.get('time'):
        self.recording_start = datetime.strptime(self._control.recording.get('date') + 'T'
                                               + self._control.recording.get('time'), '%m.%d.%YT%H.%M.%S')
      else:
        self.recording_start = datetime.strptime(self._control.recording.get('date'), '%m.%d.%Y')

    if self._control.patient.get('id') or self._control.patient.get('name'):
      p = [ ]
      if self._control.patient.get('id'):
        p.append(self._control.patient.get('id'))
      if (self._control.patient.get('name') and
          self._control.patient.get('id') != self._control.patient.get('name')):
        p.append(self._control.patient.get('name'))
      if self._control.patient.get('age'):
        p.append('Age: ' + self._control.patient.get('age'))
      self.investigation = 'Patient: ' + ', '.join(p)


    for n, d in enumerate(self._control.datafile):
      # check control.patient == d.patient
      #   and control.recording == d.recording
      try:
        # Don't have data files when PUT of control file....
        self.add_signal(SDFSignal(str(self.uri) + '/signal/%d' % (n+1),
                                  fpath + d['name'],
                                  d.get('label', None) ))
      except IOError:
        pass

    #for e in self._control.eventfile:
    #  # check control.patient == e.patient
    #  #   and control.recording == e.recording
    #  self.add_event(....)s.append(DataFile(fpath + e['name'], e.get('label', None)))

  def close(self):
  #---------------
    self._control.close()
