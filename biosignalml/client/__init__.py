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
The ``biosignalml.client`` package provides high-level interfaces to a
BioSignalML repository, allowing recordings, signals and associated resources
to be stored and retrieved.

To create a new recording and signals::

  # Connect to a repository (which is identified by a web address):
  repository = Repository("http://demo.biosignalml.org")

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

  repository = Repository("http://demo.biosignalml.org")

  # Retrieve the recording and all metadata about its signals:
  recording = repository.get_recording("http//example.org/recording/demo/1")

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
import urlparse
import numpy as np

import biosignalml
import biosignalml.rdf as rdf

from biosignalml            import BSML
from biosignalml.data       import TimeSeries, UniformTimeSeries, DataSegment
from biosignalml.data.time  import Interval
from biosignalml.formats    import BSMLRecording, BSMLSignal, MIMETYPES
from biosignalml.transports import WebStreamReader, WebStreamWriter, StreamException
from biosignalml.transports.stream import BlockType, SignalData


from . import repository


__all__ = [ 'Repository', 'Recording', 'Signal' ]


class Signal(BSMLSignal):
#========================
  """A Signal in a :class:`Recording`."""

  def __init__(self, uri, units=None, **kwds):
  #-------------------------------------------
    repository = kwds.pop('repository', None)
    self._length = 0
    super(Signal, self).__init__(uri, units, **kwds)
    self.repository = repository

  def __len__(self):
  #----------------
    return self._length

  def read(self, interval=None, segment=None, maxpoints=0, dtype=None, rate=None, units=None):
  #-------------------------------------------------------------------------------------------
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
    if dtype is not None: params['dtype'] = dtype
    if rate is not None: params['rate'] = rate
    if units is not None: params['units'] = units
    for sd in self.repository.get_data(str(self.uri), **params):
      if sd.uri != str(self.uri):
        raise StreamExeception("Received signal '%s' different from requested '%s'" % (sd.uri, self.uri))
      if sd.rate is not None: yield DataSegment(sd.start, UniformTimeSeries(sd.data, sd.rate))
      else:                   yield DataSegment(sd.start, TimeSeries(sd.data, sd.clock))

  def append(self, timeseries, dtype='f4'):
  #----------------------------------------
    self._length += len(timeseries)
    if isinstance(timeseries, TimeSeries):
      return self.repository.put_data(str(self.uri), timeseries, dtype=dtype)
    elif self.rate:
      return self.repository.put_data(str(self.uri), UniformTimeSeries(timeseries, self.rate), dtype=dtype)


class Recording(BSMLRecording):
#==============================

  SignalClass = Signal      #: The class of signals in the recording.

  def __init__(self, *args, **kwds):
  #---------------------------------
    repository = kwds.pop('repository', None)
    super(Recording, self).__init__(*args, **kwds)
    self.repository = repository

  def close(self):
  #---------------
    # Ensure all metadata has been POSTed
    self.repository.post_metadata(self.uri, self.metadata_as_string())
    ## POST duplicates duration but leaves dataset...
    ## PUT removes dataset,,,

  def add_signal(self, signal):
  #----------------------------
    signal.repository = self.repository
    super(Recording, self).add_signal(signal)

  def new_signal(self, uri, units, id=None, **kwds):
  #-------------------------------------------------
    # And if signal uri is
    # then when server processes PUT for a new signal of BSML Recording
    # it will create an signal group in HDF5 container
    try:
      sig = super(Recording, self).new_signal(uri, units, id=id, repository=self.repository, **kwds)
      ## This should spot duplicates

      #logging.debug('New Signal: %s --> %s', sig.uri, sig.attributes)
      self.repository.post_metadata(self.uri, sig.metadata_as_string())
      return sig
    except Exception, msg:
      raise IOError("Cannot create Signal '%s' in repository" % uri)

  def save_metadata(self, metadata=None, format=rdf.Format.RDFXML):
  #----------------------------------------------------------------
    if metadata is None: metadata = self.metadata_as_string()
    self.repository.post_metadata(self.uri, metadata, format)



class Repository(repository.RemoteRepository):
#=============================================

  ## Can a Repository by stateless, created on-the-fly as needed??
  ## Then get/new methods would be static

  RecordingClass = Recording      #: The class of recordings in the repository.

  def __init__(self, uri, name=None, password=None, **kwds):
  #---------------------------------------------------------
    p = urlparse.urlparse(uri)
    if p.scheme == '' or p.hostname is None:
      raise IOError("Invalid URI -- %s" % uri)
    uri = p.scheme + '://' + p.hostname
    kwds['port'] = p.port
    super(Repository, self).__init__(uri, name=name, password=password, **kwds)

  def get_recording(self, uri, graph_uri=None, **kwds):
  #----------------------------------------------------
    rec = super(Repository, self).get_recording(uri,
            graph_uri=graph_uri,
            recording_class=self.RecordingClass,
            repository=self,
            **kwds)
    if rec is None: raise IOError("No Recording for: %s" % uri)
    return rec

  def new_recording(self, uri, **kwds):
  #------------------------------------
    try:
      rec = self.RecordingClass(uri, repository=self, **kwds)
      # Will have default metadata with attributes set from any metadata keyword dict
      rec.graph = rdf.Graph(self.put_metadata(rec.uri, rec.metadata_as_string()))
      rec.format = MIMETYPES.HDF5
      # Format = HDF5 (BSML ??)
      # then when server processes PUT for a new BSML recording it will create an empty HDF5 container
      return rec
    except Exception, msg:
      raise IOError("Cannot create Recording '%s' in repository -- %s" % (uri, msg))

  def get_signal(self, uri, graph_uri=None, **kwds):
  #-------------------------------------------------
    sig = super(Repository, self).get_signal(uri,
            graph_uri=graph_uri,
            signal_class=self.RecordingClass.SignalClass,
            repository=self,
            **kwds)
    if sig is None: raise IOError("Unknown signal: %s" % uri)
    return sig

  def _web_sockets_uri(self, uri):
  #===============================
    uri = self._sd_uri + uri
    if uri.startswith('http'): return uri.replace('http', 'ws', 1)
    else:                      return uri

  def get_data(self, uri, **kwds):
  #-------------------------------
    """ Gets :class:`~biosignalml.data.DataSegment`\s from the remote repository. """
    '''
    maxsize
    start
    duration
    offset
    count
    dtype
    rate
    units
    '''
    reader = WebStreamReader(self._web_sockets_uri(uri), uri, token=self.access_token, **kwds)
    for block in reader:
      if block.type == BlockType.DATA: yield block.signaldata()
    reader.join()

  def put_data(self, uri, timeseries, dtype='f4'):
  #-----------------------------------------------
    stream = None
    try:
      stream = WebStreamWriter(self._web_sockets_uri(uri), token=self.access_token)
      MAXPOINTS = 10000
      params = { 'dtype': dtype }
      if hasattr(timeseries, 'rate'): params['rate'] = timeseries.rate
      pos = 0
      count = len(timeseries)
      while count > 0:
        blen = min(count, MAXPOINTS)
        if hasattr(timeseries, 'clock'):
          params['clock'] = timeseries.clock[pos:pos+blen]
        stream.write_signal_data(SignalData(uri, timeseries.time[pos], timeseries.data[pos:pos+blen], **params))
        pos += blen
        count -= blen
    except Exception, msg:
      logging.error('Error in stream: %s', msg)
      raise
    finally:
      if stream: stream.close()


if __name__ == "__main__":
#=========================

##  logging.getLogger().setLevel('DEBUG')

  repo = Repository('http://devel.biosignalml.org')

  rec_uri = 'http://devel.biosignalml.org/fph/icon/120312170352/FLW0002'
  sig_uri = rec_uri + '/signal/2'

  rec = repo.get_recording(rec_uri)
  for s in sorted(rec.signals(), key=lambda s: str(s.uri)):
    print s.uri, s.label
#    for d in s.read(): print d

  sig = repo.get_signal(sig_uri)
  for d in sig.read(dtype='f4'):
    print d
