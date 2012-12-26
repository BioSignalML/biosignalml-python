######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: c1bb582 on Tue May 1 10:48:29 2012 +1200 by Dave Brooks $
#
######################################################

import math
import logging

import biosignalml.rdf as rdf
from biosignalml import BSML
from biosignalml.formats import BSMLRecording, BSMLSignal
from biosignalml.data import DataSegment, UniformTimeSeries, TimeSeries, Clock, UniformClock

from h5recording import H5Recording


class HDF5Signal(BSMLSignal):
#============================
  """
  A :class:`~biosignalml.Signal` in a HDF5 Recording.

  :param uri: The signal's URI.
  :param units: The physical units of the signal's data.
  :param kwds: Other :class:`~biosignalml.Signal` attributes to set.
  """
  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    BSMLSignal.__init__(self, uri, units, **kwds)
    self._h5 = None

  def __len__(self):
  #-----------------
    """
    Get the number of data points in a signal.
    """
    return len(self._h5) if self._h5 is not None else 0

  def _set_h5_signal(self, h5):
  #----------------------------
    self._h5 = h5
    if   h5.clock: self.clock = Clock(h5.clock.uri, h5.clock)
    elif h5.rate:  self.clock = UniformClock(None, h5.rate)

  @classmethod
  def create_from_H5Signal(cls, index, signal):
  #--------------------------------------------
    """
    Create a new signal from a signal dataset in a
    BioSignalML HDF5 file.
    """
    self = cls(signal.uri, signal.units, rate=signal.rate, clock=signal.clock)
    self._set_h5_signal(signal)
    return self

  def read(self, interval=None, segment=None, maxduration=None, maxpoints=None):
  #-----------------------------------------------------------------------------
    """
    Read data from a signal.

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
      raise ValueError("'interval' and 'segment' cannot both be specified")
    if maxduration:
      pts = int(self.rate*maxduration + 0.5)
      if maxpoints: maxpoints = min(maxpoints, pts)
      else: maxpoints = pts
    if maxpoints is None or not (0 < maxpoints <= BSMLSignal.MAXPOINTS):
      maxpoints = BSMLSignal.MAXPOINTS

    # We need to be consistent as to what an interval is....
    # Use model.Interval ??
    if interval is not None:
      segment = (self.clock.index(interval.start), self.clock.index(interval.end))

    if segment is None:
      startpos = 0
      length = len(self)
    else:
      if segment[0] <= segment[1]: seg = segment
      else:                        seg = (segment[1], segment[0])
      ##startpos = max(0, int(math.floor(seg[0])))
      startpos = max(0, seg[0])
      length = min(len(self), seg[1]+1) - startpos

    while length > 0:
      if maxpoints > length: maxpoints = length
      data = self._h5[startpos: startpos+maxpoints]
      if isinstance(self.clock, UniformClock):
        yield DataSegment(self.clock[startpos], UniformTimeSeries(data, self.clock.rate))
      else:
        yield DataSegment(0, TimeSeries(data, self.clock[startpos: startpos+maxpoints]))
      startpos += len(data)
      length -= len(data)

  def initialise(self):
  #--------------------
    """
    Set signal attributes once the HDF5 file of its recording is opened.
    """
    self._set_h5_signal(self.recording._h5.get_signal(self.uri))

  def append(self, timeseries):
  #----------------------------
    '''
    Append data to a signal.

    :param timeseries: The data points (and times) to append.
    :type timeseries: :class:`~biosignalml.data.TimeSeries`
    '''
    if self.clock and not isinstance(self.clock, UniformClock):
      self.recording._h5.extend_clock(self.clock.uri, timeseries.time.times)
    self.recording._h5.extend_signal(self.uri, timeseries.data)


class HDF5Recording(BSMLRecording):
#==================================
  """
  A HDF5 :class:`~biosignalml.Recording`.

  :param uri: The recording's URI.
  :param dataset: The file path or URI of the BioSignalML HDF5 file for the recording.
  :param kwds: :class:`~biosignalml.Recording` attributes to set.
  """

  MIMETYPE = 'application/x-bsml+hdf5'   #: The mimetype for BioSignalML HDF5 files
  EXTENSIONS = [ 'h5', 'hdf', 'hdf5' ]   #: File extensions to try when opening a file
  SignalClass = HDF5Signal               #: The class of Signals HDF5Recording

  def __init__(self, uri, dataset=None, **kwds):
  #---------------------------------------------
    ## What about self.load_metadata() ???? Do kwds override ??
    BSMLRecording.__init__(self, uri, dataset, **kwds)
    if dataset:
      self._h5 = self._openh5(dataset)
      if uri is not None and str(uri) != str(self._h5.uri):
        raise TypeError("Wrong URI in HDF5 recording")
      ## What about self.load_metadata() ???? Do kwds override ??
      for n, s in enumerate(self._h5.signals()):
        self.add_signal(HDF5Signal.create_from_H5Signal(n, s))
    else:
      self._h5 = None

  def _openh5(self, fname):
  #------------------------
    try:            return H5Recording.open(fname)
    except IOError: return H5Recording.create(self.uri, fname)

  @classmethod
  def open(cls, dataset, **kwds):
  #------------------------------
    """
    Open a BioSignalML HDF5 file to obtain a HDF5 Recording.

    :param dataset: The file path or URI of the BioSignalML HDF5 file.
    :param kwds: Other :class:`~biosignalml.Recording` attributes to set.
    """
    return cls(None, dataset, **kwds)

  @classmethod
  def create(cls, uri, dataset, **kwds):
  #-------------------------------------
    """
    Create a new recording and its BioSignalML HDF5 file.

    :param uri: The recording's URI.
    :param dataset: The file path or URI of the BioSignalML HDF5 file.
    :param kwds: Other :class:`~biosignalml.Recording` attributes to set.
    """
    self = cls(uri, None, **kwds)
    self.dataset = dataset
    self._h5 = H5Recording.create(uri, str(dataset))
    return self

  def close(self):
  #---------------
    """ Close a recording`. """
    if self._h5:
      self._h5.close()
      self._h5 = None

  def new_signal(self, uri, units, id=None, **kwds):
  #-------------------------------------------------
    """
    Create a new signal and add it to the recording.

    :param uri: The URI for the signal.
    :param units: The physical units of the signal's data.
    :rtype: :class:`HDF5Signal`
    :param kwds: Other :class:`~biosignalml.Signal` attributes to set.
    """
    sig = BSMLRecording.new_signal(self, uri, units, id=id, **kwds)
    if self._h5:
      if sig.clock: self._h5.create_clock(sig.clock.uri)
      sig._h5 = self._h5.create_signal(sig.uri, units, **kwds)
    return sig

  def save_metadata(self, format=rdf.Format.TURTLE, prefixes=None):
  #----------------------------------------------------------------
    """
    Save all metadata associated with the recording in its
    BioSignalML HDF5 file.

    :param format: The :class:`~biosignalml.rdf.Format` in which to serialise RDF.
    :param prefixes: An optional dictionary of namespace abbreviations and URIs.
    """
    self._h5.store_metadata(self.metadata_as_string(format=format, prefixes=prefixes),
                        rdf.Format.mimetype(format))

  def load_metadata(self):
  #-----------------------
    """
    Set metadata attributes of the recording from its associated
    BioSignalML HDF5 file.
    """
    rdf, format = self._h5,get_metadata()
    if rdf:
      self.load_from_graph(rdf.Graph.create_from_string(self.uri, rdf, format))

  def initialise(self, **kwds):
  #----------------------------
    """
    Set recording and associated signal attributes
    once the recording's dataset is known.
    """
    if self.dataset is not None:
      self._h5 = self._openh5(str(self.dataset))
      for s in self.signals():
        HDF5Signal.initialise_class(s)

