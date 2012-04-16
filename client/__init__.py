######################################################
#
#  BioSignalML Project
#
#  Copyright (c) 2010-2012  David Brooks
#
#  $ID$
#
######################################################
"""
High level interfaces to a BioSignalML repository.

This package simplifies creating and reading signals in a repository
by providing wrappers around connections to metadata and data endpoints.

To create a new recording and signals::

  # Connect to a repository (which is identified by a web address):
  repository = Repository.connect("http://demo.biosignalml.org")

  # Create a new recording in the repository, specifying a URI to identify it:
  recording = repository.new_recording("http//example.org/recording/demo/1",
                                       description="This is an example")
  # Metadata attributes can be set either as keywords when the recording is created or
  # by assignment:
  recording.metadata.age = 59

  # Create a new signal in the recording, specifying an identifier (that will be expanded
  # to a full URI) and the physical units of its data:
  signal1 = recording.new_signal(None, UNITS.mV, id="id1")
  # Metadata attributes can also be assigned:
  signal1.label = "ECG"
  # Create a second signal:
  signal2 = recording.new_signal(None, UNITS.mbar, id="id2", label="Pressure")

  # Append time series data (timing information is part of a time series):
  signal1.append(data1)
  signal2.append(data2)
  # Continue appending data...

  # When all done ensure everything is stored:
  recording.close()
  repository.close()

And to get back signal data::

  repository = Repository.connect("http://demo.biosignalml.org")

  # Retrieve the recording and all metadata about its signals:
  recording = repository.get_recording_with_signals("http//example.org/recording/demo/1")

  # Select a signal by its signal identifier (can also use a URI):
  signal = recording.signal(id="id2")

  # Print some information about the recording and signal:
  print recording.description, signal.uri, signal.label, signal.units

  # Retrieve and print time series data for the first second of the signal:
  for data in sig.read((0.0, 1.0)):
    print data

  # All done:
  recording.close()
  repository.close()
"""

import logging
import numpy as np

import biosignalml
import biosignalml.rdf as rdf

from biosignalml            import BSML
from biosignalml.data       import TimeSeries, UniformTimeSeries, DataSegment
from biosignalml.timeline   import Interval
from biosignalml.formats    import BSMLRecording, BSMLSignal
from biosignalml.transports import StreamException

import repository


class Signal(BSMLSignal):
#========================

  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    repository = kwds.pop('repository', None)
    BSMLSignal.__init__(self, uri, units, **kwds)
    self.repository = repository

  def close(self):
  #---------------
    # Ensure all metadata has been POSTed
    pass

  def read(self, interval=None, segment=None, maxpoints=0):
  #--------------------------------------------------------
    params = { }
    if interval:
      if isinstance(interval, Interval):
        params['start'] = interval.start
        params['duration'] = interval.duration
      else:
        params['start'] = interval[0]
        params['duration'] = interval[1]
    if segment:
      params['offset'] = segment[0]
      params['count'] = segment[1]
    if maxpoints: params['maxsize'] = maxpoints
    for sd in self.repository.get_data(str(self.uri), **params):
      if str(sd.uri) != str(self.uri):
        raise StreamExeception("Received signal '%s' different from requested '%s'" % (sd.uri, self.uri))
      if sd.rate is not None: yield DataSegment(sd.start, UniformTimeSeries(sd.data, sd.rate))
      else:                   yield DataSegment(sd.start, TimeSeries(sd.clock, sd.data))

  def append(self, timeseries):
  #----------------------------
    if isinstance(timeseries, np.ndarray) and self.rate:
      return self.repository.put_data(str(self.uri), UniformTimeSeries(timeseries, self.rate))
    else:
      return self.repository.put_data(str(self.uri), timeseries)


class Recording(BSMLRecording):
#==============================

  SignalClass = Signal      #: The class of signals in the recording.
  FORMAT = BSML.BSML_HDF5   #: Stored in :class:`~biosignalml.formats.hdf5.HDF5Recording` format.

  def __init__(self, *args, **kwds):
  #---------------------------------
    repository = kwds.pop('repository', None)
    BSMLRecording.__init__(self, *args, **kwds)
    self.repository = repository

  def close(self):
  #---------------
    # Ensure all metadata has been POSTed
    pass

  def new_signal(self, uri, units, id=None, **kwds):
  #-------------------------------------------------
    # And if signal uri is
    # then when server processes PUT for a new signal of BSML Recording
    # it will create an signal group in HDF5 container
    try:
      sig = BSMLRecording.new_signal(self, uri, units, id=id, repository=self.repository, **kwds)
      ## This should spot duplicates, even if we have done get_recording()
      ## and not get_recording_with_signals()

      logging.debug('New Signal: %s --> %s', sig.uri, sig.attributes)
      sig.repository.post_metadata(self.uri, sig.metadata_as_graph())
      return sig
    except Exception, msg:
      raise
      raise IOError("Cannot create Signal '%s' in repository" % uri)


class Repository(repository.RemoteRepository):
#=============================================

  RecordingClass = Recording      #: The class of recordings in the repository.

  def get_recording(self, uri, **kwds):
  #------------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Recording)):
      return self.RecordingClass.create_from_graph(uri, graph, repository=self, **kwds)


  def get_recording_with_signals(self, uri, **kwds):
  #-------------------------------------------------
    rec = self.get_recording(uri, **kwds)
    if rec is not None:
      for sig in rec.graph.get_subjects(BSML.recording, rdf.Uri(uri)):
        rec.set_signal(
          self.RecordingClass.SignalClass.create_from_graph(
            sig.uri, self.get_metadata(sig.uri), units=None, repository=self))
    return rec

  def new_recording(self, uri, **kwds):
  #------------------------------------
    try:
      rec = self.RecordingClass(uri, repository=self, **kwds)
      # Will have default metadata with attributes set from any metadata keyword dict
      self.put_metadata(rec.uri, rec.metadata_as_graph())
      # Format = HDF5 (BSML ??)
      # then when server processes PUT for a new BSML recording it will create an empty HDF5 container
      return rec
    except Exception, msg:
      raise IOError("Cannot create Recording '%s' in repository" % uri)


  def store_recording(self, rec):       ## or save_recording ??
  #------------------------------
    self.put_metadata(rec.uri, rec.save_to_graph())


  def get_signal(self, uri, **kwds):
  #---------------------------------
    graph = self.get_metadata(uri)
    if graph.contains(rdf.Statement(uri, rdf.RDF.type, BSML.Signal)):
      sig = self.RecordingClass.SignalClass.create_from_graph(uri, self.get_metadata(uri), repository=self)
      sig.recording = self.get_recording(sig.recording)
      return sig

