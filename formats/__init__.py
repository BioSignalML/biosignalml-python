'''
Read and write physical Recordings and Signals.
'''
######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
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
#  $ID$
#
######################################################

import biosignalml.model as model
from biosignalml.model import BSML, TimeSeries
from biosignalml.utils import file_uri


def not_implemented(instance, method):
#=====================================
  '''
  Raise an Exception for unimplemented methods.
  '''
  raise NotImplementedError('%s.%s()' % (instance.__class__.__name__, method))


class BSMLRecording(model.Recording):
#====================================
  '''
  A generic biosignal Recording as a physical object.

  :param fname: Name of filesystem object holding a Recording.
  :type fname: str
  :param uri: URI of the Recording.
  :type uri: str
  :param mode: Open the recording for reading ('r') or create a new recording ('w').
  :type mode: str
  :param metadata: Dictionary containing metadata values for the recording.
  :type metadata: dict

  If `fname` is set but not `metadata['source']` then `source` is set to
  the full 'file://' path of `fname`; if `uri` is not given it is set to `source`.

  If no `fname` and no `metadata['source']` then `source` is set to `uri`.
  '''
  def __init__(self, fname=None, uri=None, mode='r', metadata={}):
  #---------------------------------------------------------------
    if fname:
      if 'source' not in metadata: metadata['source'] = file_uri(fname)
      if not uri: uri = metadata['source']
    elif 'source' not in metadata:
      metadata['source'] = uri
    if 'format' not in metadata: metadata['format'] = BSML.RAW
    super(BSMLRecording, self).__init__(uri, metadata=metadata)
    if metadata.get('digest'): self.metadata['digest'] = metadata['digest']

  @classmethod
  def open(cls, fname, uri=None, mode='r', **kwds):
  #------------------------------------------------
    '''
    Open a Recording.

    :param fname: Name of filesystem object holding the recording.
    :type fname: str
    :param uri: URI of the recording.
    :type uri: str
    :param mode: Open the recording for reading ('r') or create a new recording ('w').
    :type mode: str
    :return: a biosignal Recording.
    '''
    return cls(fname, uri=uri, mode=mode, **kwds)

  @classmethod
  def create(cls, fname, uri=None, **kwds):
  #----------------------------------------
    '''
    Create a Recording.

    :param fname: Name of filesystem object holding a Recording.
    :type fname: str
    :param uri: URI of the Recording.
    :type uri: str
    :return: a new biosignal Recording (with no Signals).
    '''
    return cls.open(fname, uri=uri, mode='w', **kwds)

  def close(self):
  #---------------
    '''
    Close a Recording.
    '''
    pass

  def rdf_metadata(self, format='turtle', prefixes={}):
  #----------------------------------------------------
    """
    Get a Recording's metadata as RDF.

    :param format: The RDF format with which to serialise metadata. Options are 'turtle'
      and 'rdfxml'.
    :type format: str
    :return: The RDF as a string.
    :rtype: str
    """
    not_implemented(self, 'save_metadata')


class BSMLSignal(model.Signal):
#==============================
  '''
  A generic biosignal Signal as a physical object.

  :param uri: URI of the signal.
  :type uri: str
  :param metadata: Dictionary containing metadata values for the signal.
  :type metadata: dict
  '''

  def __init__(self, uri, metadata={}):
  #------------------------------------
    super(BSMLSignal, self).__init__(uri, metadata=metadata)

  def read(self, interval=None):
  #-----------------------------
    '''
    Read data from a Signal.

    :param interval: The portion of the signal to read.
    :return: A TimeSeries containing signal data covering the interval.
    :rtype: :class:`TimeSeries`

    The `interval` to be read can be given as either a temporal interval or as data indices.
    '''
    not_implemented(self, 'read')

  def append(self, timeseries):
  #----------------------------
    '''
    Append data to a Signal.

    :param timeseries: The data points (and times) to append.
    :type timeseries: :class:`TimeSeries`
    '''
    not_implemented(self, 'append')

  def data(self, n):
  #----------------
    '''
    Get a single data point in a Signal.

    :param n: The index of the data point.
    :type n: non-negative integer
    :return: The value of the n\ :sup:`th` data point.
    '''
    not_implemented(self, 'data')

  def time(self, n):
  #----------------
    '''
    Get the time of a data point in a Signal.

    :param n: The index of the data point.
    :type n: non-negative integer
    :return: The time of the n\ :sup:`th` data point.
    '''
    not_implemented(self, 'time')


from raw  import RAWRecording
from edf  import EDFRecording
from sdf  import SDFRecording
from wfdb import WFDBRecording
from hdf5 import HDF5Recording
