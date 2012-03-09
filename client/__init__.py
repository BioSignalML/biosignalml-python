######################################################
#
#  BioSignalML Project
#
#  Copyright (c) 2010-2012  David Brooks
#
#  $ID$
#
######################################################

import logging

import biosignalml
import biosignalml.rdf as rdf

from biosignalml            import BSML
from biosignalml.data       import TimeSeries, UniformTimeSeries, DataSegment
from biosignalml.formats    import BSMLRecording, BSMLSignal
from biosignalml.transports import StreamException

import repository


class Recording(BSMLRecording):
#==============================

  def __init__(self, *args, **kwds):
  #---------------------------------
    repository = kwds.pop('repository', None)
    BSMLRecording.__init__(self, *args, **kwds)
    self.repository = repository
    # Format = HDF5 (BSML ??)

  def close(self):
  #---------------
    # Ensure all metadata has been POSTed
    pass

  def new_signal(self, uri=None, id=None, **kwds):
  #-----------------------------------------------
    # And if signal uri is
    # then when server processes PUT for a new signal of BSML Recording
    # it will create an signal group in HDF5 container
    try:
      if uri is None: uri = self.uri + '/signal/' + id
      sig = BSMLRecording.new_signal(self, uri, Signal, repository=self.repository, **kwds)
      ## This should spot duplicates, even if we have done get_recording()
      ## and not get_recording_with_signals()

      logging.debug('New Signal: %s --> %s', sig.uri, sig.attributes)
      sig.repository.post_metadata(sig.uri, sig.metadata_as_graph())
      return sig
    except Exception, msg:
      raise IOError("Cannot create Signal '%s' in repository" % uri)


class Signal(BSMLSignal):
#========================

  def __init__(self, *args, **kwds):
  #---------------------------------
    repository = kwds.pop('repository', None)
    BSMLSignal.__init__(self, *args, **kwds)
    self.repository = repository

  def close(self):
  #---------------
    # Ensure all metadata has been POSTed
    pass

  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    params = { 'maxsize': points }
    if interval:
      params['start'] = interval.start
      params['duration'] = interval.duration
    if segment:
      params['offset'] = segment[0]
      params['count'] = segment[1]
    for sd in self.repository.get_data(str(self.uri), **params):
      if str(sd.uri) != str(self.uri):
        raise StreamExeception("Received signal '%s' different from requested '%s'" % (sd.uri, self.uri))
      if sd.rate is not None: yield DataSegment(sd.start, UniformTimeSeries(sd.data, sd.rate))
      else:                   yield DataSegment(sd.start, TimeSeries(sd.clock, sd.data))

  def append(self, timeseries):
  #----------------------------
    return self.repository.put_data(str(self.uri), timeseries)


class Repository(repository.RemoteRepository):
#=============================================

  def get_recording(self, uri, **kwds):
  #------------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Recording)):
      return Recording.create_from_graph(uri, graph, repository=self, **kwds)


  def get_recording_with_signals(self, uri, **kwds):
  #-------------------------------------------------
    rec = self.get_recording(uri, **kwds)
    if rec is not None:
      for sig in rec.graph.get_subjects(BSML.recording, rdf.Uri(uri)):
        rec.set_signal(Signal.create_from_graph(sig.uri, self.get_metadata(sig.uri), repository=self))
    return rec

  def new_recording(self, uri, **kwds):
  #------------------------------------
    try:
      rec = Recording(uri, repository=self, **kwds)
      # Will have default metadata with attributes set from any metadata keyword dict
      self.put_metadata(rec.uri, rec.metadata_as_graph())
      # Format = HDF5 (BSML ??)
      # then when server processes PUT for a new BSML recording it will create an empty HDF5 container
      return rec
    except Exception, msg:
      raise IOError("Cannot create Recording '%s' in repository" % uri)


  def store_recording(self, uri, **kwds):       ## or save_recording ??
  #------------------------------------
    rec = Recording(uri, repository=self, **kwds)
    # Will have default metadata with attributes set from any metadata keyword dict
    self.put_metadata(rec.uri, rec.save_to_graph())


  def get_signal(self, uri, **kwds):
  #---------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Signal)):
      sig = Signal.create_from_graph(uri, self.get_metadata(uri), repository=self)
      sig.recording = self.get_recording(sig.recording)
      return sig

