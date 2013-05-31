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
Read and write physical Recordings and Signals.
"""

import os

import biosignalml
from biosignalml import BSML
from biosignalml.utils import file_uri
import biosignalml.model.mapping as mapping

__all__ = [ 'BSMLSignal', 'BSMLRecording', 'MIMETYPES' ]


def _not_implemented(instance, method):
#======================================
  """
  Raise an Exception for unimplemented methods.
  """
  raise NotImplementedError('%s.%s()' % (instance.__class__.__name__, method))


class BSMLSignal(biosignalml.Signal):
#====================================
  """
  A generic biosignal Signal as a physical object.

  :param uri: The URI of the signal.
  :param units: The signal's measurement units.
  :param kwds: Attributes of a :class:`~biosignalml.Signal`.
  """

  MAXPOINTS = 50000     #: Maximum number of sample points returned by a single :meth:`read`.

  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    biosignalml.Signal.__init__(self, uri, units, **kwds)

  def close(self):
  #---------------
    """Close a Signal."""
    pass

  def read(self, interval=None, segment=None, maxduration=None, maxpoints=None):
  #-----------------------------------------------------------------------------
    """
    Read data from a Signal.

    :param interval: The portion of the signal to read.
    :type interval: :class:`~biosignaml.time.Interval`
    :param segment: A 2-tuple with start and finishing data indices, with the end
      point not included in the returned range.
    :param maxduration: The maximum duration, in seconds, of a single returned segment.
    :param maxpoints: The maximum length, in samples, of a single returned segment.
    :return: An ``iterator`` returning :class:`~biosignalml.data.DataSegment` segments
      of the signal data.

    If both ``maxduration`` and ``maxpoints`` are given their minimum value is used.
    """
    _not_implemented(self, 'read')

  def append(self, timeseries):
  #----------------------------
    """
    Append data to a Signal.

    :param timeseries: The data points (and times) to append.
    :type timeseries: :class:`~biosignalml.data.TimeSeries`
    """
    _not_implemented(self, 'append')

  def data(self, n):
  #----------------
    """
    Get a single data point in a Signal.

    :param n: The index of the data point.
    :type n: non-negative integer
    :return: The value of the n\ :sup:`th` data point.
    """
    _not_implemented(self, 'data')

  def time(self, n):
  #----------------
    """
    Get the time of a data point in a Signal.

    :param n: The index of the data point.
    :type n: non-negative integer
    :return: The time of the n\ :sup:`th` data point.
    """
    _not_implemented(self, 'time')


class BSMLRecording(biosignalml.Recording):
#==========================================
  """
  A generic biosignal Recording as a physical object.

  :param fname: Name of filesystem object holding a Recording.
  :type fname: str
  :param uri: URI of the Recording.
  :type uri: str
  :param mode: Open the recording for reading ('r') or create a new recording ('w').
  :type mode: str
  """
  MIMETYPE = 'application/x-bsml'
  EXTENSIONS = [ 'bsml' ]
  SignalClass = BSMLSignal
  attributes = [ 'digest', 'dataset' ]
  mapping    = { 'dataset': mapping.PropertyMap(BSML.dataset) }

  def __init__(self, uri=None, dataset=None, mode='r', **kwds):
  #------------------------------------------------------------
    if dataset:
      dataset = file_uri(dataset)
      if not uri: uri = dataset
    kwds['dataset'] = dataset
    kwds['format'] = getattr(self, 'MIMETYPE')
    biosignalml.Recording.__init__(self, uri, **kwds)

  def __del__(self):
  #-----------------
    self.close()

  @classmethod
  def open(cls, dataset, uri=None, mode='r', **kwds):
  #------------------------------------------------
    """
    Open a Recording.

    :param dataset: Name of filesystem object holding the recording.
    :type dataset: str
    :param uri: URI of the recording.
    :type uri: str
    :param mode: Open the recording for reading ('r') or create a new recording ('w').
    :type mode: str
    :return: a biosignal Recording.
    """
    return cls(uri=uri, dataset=dataset, mode=mode, **kwds)

  @classmethod
  def create(cls, dataset, uri=None, **kwds):
  #----------------------------------------
    """
    Create a Recording.

    :param dataset: Name of filesystem object holding a Recording.
    :type dataset: str
    :param uri: URI of the Recording.
    :type uri: str
    :return: a new biosignal Recording (with no Signals).
    """
    return cls.open(uri=uri, dataset=dataset, mode='w', **kwds)

  def close(self):
  #---------------
    """
    Close a Recording.
    """
    pass


class MIMETYPES(object):
#=======================

  EDF  = 'application/x-bsml+edf'    ## EDF+ as well...   #### look at self.edf_type ??
  HDF5 = 'application/x-bsml+hdf5'   #: The mimetype for BioSignalML HDF5 files
  RAW  = 'application/x-bsml+raw'
  WFDB = 'application/x-bsml+wfdb'



CLASSES = { }
#============

try:
  from edf  import EDFRecording
  CLASSES[MIMETYPES.EDF] = EDFRecording
except ImportError:
  pass

try:
  from hdf5 import HDF5Recording
  CLASSES[MIMETYPES.HDF5] = HDF5Recording
except ImportError:
  pass

try:
  from raw import RAWRecording
  CLASSES[MIMETYPES.RAW] = RAWRecording
except ImportError:
  pass

try:
  from wfdb import WFDBRecording
  CLASSES[MIMETYPES.WFDB] = WFDBRecording
except ImportError:
  pass

##from sdf  import SDFRecording
