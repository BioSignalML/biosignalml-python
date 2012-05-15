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
#  $ID: 60c35bd on Tue May 1 11:33:00 2012 +1200 by Dave Brooks $
#
######################################################

import biosignalml
from biosignalml import BSML
from biosignalml.utils import file_uri


def not_implemented(instance, method):
#=====================================
  '''
  Raise an Exception for unimplemented methods.
  '''
  raise NotImplementedError('%s.%s()' % (instance.__class__.__name__, method))


class BSMLRecording(biosignalml.Recording):
#==========================================
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

  attributes = [ 'digest' ]

  FORMAT = BSML.RAW
  MIMETYPE = 'application/x-raw'
  EXTENSIONS = [ 'raw' ]

  def __init__(self, uri=None, fname=None, mode='r', metadata=None, **kwds):
  #-------------------------------------------------------------------------
    if fname:
      if 'source' not in kwds: kwds['source'] = file_uri(fname)
      if not uri: uri = kwds['source']
    elif 'source' not in kwds:
      kwds['source'] = uri
    kwds['format'] = getattr(self, 'FORMAT')
    biosignalml.Recording.__init__(self, uri, metadata=metadata, **kwds)

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
    return cls(uri=uri, fname=fname, mode=mode, **kwds)

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
    return cls.open(uri=uri, fname=fname, mode='w', **kwds)

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


class BSMLSignal(biosignalml.Signal):
#====================================
  '''
  A generic biosignal Signal as a physical object.

  :param uri: URI of the signal.
  :type uri: str
  :param metadata: Dictionary containing metadata values for the signal.
  :type metadata: dict
  '''

  def __init__(self, uri, units, metadata=None, **kwds):
  #-----------------------------------------------------
    biosignalml.Signal.__init__(self, uri, units, metadata=metadata, **kwds)

  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    '''
    Read data from a Signal.

    :param interval: The portion of the signal to read.
    :return: A DataSegment containing signal data covering the interval.
    :rtype: :class:`~biosignalml.data.DataSegment`

    The `interval` to be read can be given as either a temporal interval or as data indices.
    '''
    not_implemented(self, 'read')

  def append(self, timeseries):
  #----------------------------
    '''
    Append data to a Signal.

    :param timeseries: The data points (and times) to append.
    :type timeseries: :class:`~biosignalml.data.TimeSeries`
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
##from sdf  import SDFRecording
from wfdb import WFDBRecording
from hdf5 import HDF5Recording

CLASSES = { str(BSML.EDF):  EDFRecording,
            str(BSML.WFDB): WFDBRecording,
            str(BSML.BSML_HDF5): HDF5Recording,
          }
