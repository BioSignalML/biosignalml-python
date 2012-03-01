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
from biosignalml.transports import WebStreamReader, StreamException


class Recording(BSMLRecording):
#==============================
  pass

class Signal(BSMLSignal):
#========================

  def __init__(self, *args, **kwds):
  #---------------------------------
    repository = kwds.pop('repository')
    BSMLSignal.__init__(self, *args, **kwds)
    self.repository = repository

  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    params = { 'maxsize': points }
    if interval:
      params['start'] = interval.start
      params['duration'] = interval.duration
    if segment:
      params[offset] = segment[0]
      params[count] = segment[1]
    for sd in self.repository.get_data(str(self.uri), **params):
      if str(sd.uri) != str(self.uri):
        raise StreamExeception("Received signal '%s' different from requested '%s'" % (sd.uri, self.uri))
      if sd.rate is not None: yield DataSegment(sd.start, UniformTimeSeries(sd.data, sd.rate))
      else:                   yield DataSegment(sd.start, TimeSeries(sd.clock, sd.data))


class Repository(object):
#========================

  def __init__(self, uri, md_endpoint='/metadata/', sd_endpoint='/stream/data/'):
  #------------------------------------------------------------------------------
    self.uri = uri
    self._md_uri = uri + md_endpoint
    self._sd_uri = uri + sd_endpoint
    self.metadata = self.get_metadata('')

  def get_metadata(self, uri):
  #---------------------------
    graph = rdf.Graph.create_from_resource(self._md_uri + str(uri), rdf.Format.RDFXML)
    if uri: graph.uri = rdf.Uri(uri)
    return graph

  def get_recording(self, uri, **kwds):
  #------------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Recording)):
      return Recording.create_from_graph(uri, graph, **kwds)

  def get_recording_with_signals(self, uri, **kwds):
  #-------------------------------------------------
    rec = self.get_recording(uri, **kwds)
    if rec is not None:
      for sig in rec.graph.get_subjects(BSML.recording, rdf.Uri(uri)):
        rec.add_signal(Signal.create_from_graph(sig.uri, self.get_metadata(sig.uri), repository=self))
    return rec

  def get_signal(self, uri, **kwds):
  #---------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Signal)):
      sig = Signal.create_from_graph(uri, self.get_metadata(uri), repository=self)
      sig.recording = self.get_recording(sig.recording)
      return sig

  def get_data(self, uri, **kwds):
  #-------------------------------
    return WebStreamReader(self._sd_uri, uri, **kwds)
