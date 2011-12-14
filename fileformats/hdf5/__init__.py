######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


"""

A single Recording per HDF5 file, either with separate datasets for
each Signal of the Recording::

  Path               Object   Type     Attributes
  ----               ------   ----     ----------
  /                  Root              version
  /metadata          Dataset  STRING   format
  /recording_uri     Group             uri
   ./signal0_uri     Dataset  Numeric  uri, rate/clock
   ./signal1_uri     Dataset  Numeric  uri, rate/clock
       .
   ./clock0_uri      Dataset  Numeric  uri
       .

and second case with simulation data inside a ./signals group::

  Path               Object   Type     Attributes
  ----               ------   ----     ----------
  /                  Root              version
  /metadata          Dataset  STRING   format
  /simulation_uri    Group             uri
   ./data            Dataset  Numeric  rate/clock
   ./clock           Dataset  Numeric
   ./uris            Dataset  STRING


Do we allow for mutiple recordings and simulations within the one file? Yes??


Need to have our code work relative to a group instead of a file's root.


"""

import h5py
import numpy as np
from numbers import Number
import logging


import model
from bsml import BSML
from fileformats import BSMLRecording, BSMLSignal

VERSION   = "1.0"

CHUNKSIZE = 4096

## Helper functions:

def _normalise_name(nm):
#-----------------------
  return str(nm).replace('/', '_')

def _make_name(prefix, nm):
#--------------------------
  if str(nm).startswith(str(prefix)):
    nm = str(nm)[len(str(prefix)):]
    if nm and nm[0] == '/': nm = nm[1:]
  return _normalise_name(nm)


def _set_clock(hdf5, attr, value):
#---------------------------------
  if attr in ['clock', 'rate']:
    if value: hdf5.attrs[attr] = value if isinstance(value, Number) else str(value)
    elif attr in hdf5.attrs: del hdf5.attrs[attr]

def _del_clock(hdf5, attr):
#--------------------------
  if attr in ['clock', 'rate'] and attr in hdf5.attrs:
    del hdf5.attrs[attr]


def _set_attribute(obj, hdf5, attr, value):
#------------------------------------------
  if (value is not None and (value != ''
         or not isinstance(value, str) and not isinstance(value, unicode))):
    ##logging.debug("Attr %s: '%s' to '%s'", hdf5, attr, value)
    object.__setattr__(obj, attr, value)
    hdf5.attrs[attr] = value if isinstance(value, Number) else str(value)
  elif attr in hdf5.attrs:
    del hdf5.attrs[attr]


class HDF5Recording(BSMLRecording):
#==================================

  def __init__(self, fname, mode, uri=None, metadata={}):
  #------------------------------------------------------
    metadata['format'] = BSML.HDF5
    super(HDF5Recording, self).__init__(fname, uri=uri, metadata=metadata)
    self._file = h5py.File(fname, mode)  # Do we allow an existing file to be extended?
    self._version = self._file.attrs.get('version')
    if self._version is None:
      self._file.attrs['version'] = VERSION
      self._version = VERSION
    self._recording = self._file.require_group(_normalise_name(self.uri))
    self._recording.attrs['uri'] = str(self.uri)
    self._recording.attrs['channels'] = -1 ;
    self._sigdata = None

  def close(self):
  #---------------
    # if new file then self.save_metadata() ??
    # and have set_metadata_format/prefixes as separate call??
    self._file.close()

  @classmethod
  def open(cls, fname, mode='r', uri=None):
  #----------------------------------------
    # If multiple recordings per file then can we add extra recordings?
    # With no extension of existing recordings??

    # read/parse metadata and add to self._graph (self._model ??)
    self = cls(fname, mode, uri=uri) ## , metadata=

    # and then add all Signals to Recording...


  @classmethod
  def create(cls, fname, mode='w-', uri=None, metadata={}):
  #--------------------------------------------------------
    # check filename extension and add '.h5' or '.hdf5'
    return cls(fname, mode, uri=uri, metadata=metadata)

  ## create_from_recording sets source to recording.uri? or recording.source??
  @classmethod
  def create_from_recording(cls, recording, fname, mode='w-'):
  #-----------------------------------------------------------
    return cls.create(fname, mode, uri=recording.uri, metadata=recording.get_metavars())

  def save_metadata(self, format='turtle', prefixes={}):
  #-----------------------------------------------------
    md = self._file.create_dataset('metadata',
           data=self.metadata_as_string(format=format, prefixes=prefixes))
    md.attrs['format'] = format

  def create_signals(self, uris, data=None, dtype=None):
  #-----------------------------------------------------
    """
    :param uris: list with uris for each signal
    :param data: list with TimeSeries for each signal's data points

    """
    if data is not None and len(data.shape) > 1 and len(uris) != data.shape[0]:
      raise Exception, "Number of Signal uris different from number of data columns"
    return [ HDF5Signal.create(uri, self, data[n] if data is not None else None, dtype)
               for n, uri in enumerate(uris) ]

  def create_signal_group(self, uris, data=None, dtype=None, dims=1, metadata={}):
  #-------------------------------------------------------------------------------
    """
    :param data: An array (1 or 2D) or a list of data points

    """
    channels = len(uris)
    if data is not None and len(data.shape) > 1 and channels != data.shape[0]:
      raise Exception, "Number of Signal uris different from number of data columns"
    self._recording.attr['channels'] = channels # So we know type of HDF5 recording
    self._recording.create_dataset('uris', data=[str(u) for u in uris], dtype=h5py.new_vlen(str))
    dataset = self._recording.create_dataset('data', dtype=dtype,
                                             shape=(channels, 0), maxshape=(channels, None,),
                                             chunks=(channels, CHUNKSIZE,) ) # CHUNKSIZE/channels ??
    self._sigdata = dataset
    if data: self.append_signal_data(data)
    return [ HDF5Signal(uri, self, dataset, metadata=metadata, index=n)
      for n, uri in enumerate(uris) ]

  def append_signal_data(self, data):
  #----------------------------------
    """
    :param data: An array (1 or 2D) or a list of data points

    """
    if self._sigdata is None: raise Exception, "Recording has no Signal group"
    end = self._sigdata.shape[1]
    if isinstance(data, list) or len(data.shape) == 1:
      step = self._sigdata.shape[0]
      self._sigdata.resize(end + len(data)/step, 1)
      for n in xrange(0, len(data), step):
        self._sigdata[..., end] = data[n:n+step]
        end += 1
    else:
      self._sigdata.resize(end + data.shape[1], 1)
      self._sigdata[..., end:] = data


class HDF5Signal(BSMLSignal):
#============================

  def __init__(self, uri, recording, dataset, metadata={}, index=None):
  #--------------------------------------------------------------------
    object.__setattr__(self, '_dset', dataset)  # Used in __setattr__()
    self._index = index
    metadata.pop('uri', None)  # In case metadata contains a uri.
    super(HDF5Signal, self).__init__(uri, metadata=metadata)
    if index is None: self._dset.attrs['uri'] = str(self.uri)
    recording.add_signal(self)

  def __setattr__(self, attr, value):
  #----------------------------------
    _set_clock(self._dset, attr, value)
    object.__setattr__(self, attr, value)

  def __delattr__(self, attr):
  #---------------------------
    _del_clock(self._dset, attr)
    object.__delattr__(self, attr)

  @classmethod
  def open(cls, recording, uri):
  #-----------------------------
    name = _make_name(recording.uri, uri)

    dataset = recording._recording[name]

    assert str(uri) == dataset.attrs['uri']


    return cls(uri, recording, dataset) # , metadata= ## get from metadata block...
                                                  ## via dataset.attrs['uri']

    dataset = recording._recording['data']
    try:
      index = recording._recording['uris'].index(str(uri))
    except ValueError:
      raise ValueError, 'Signal %s is not in Recording' % str(uri)



  @classmethod
  def create(cls, uri, recording, data=None, dtype=np.dtype('f'), metadata={}):
  #----------------------------------------------------------------------------
    dataset = recording._recording.create_dataset(_make_name(recording.uri, uri),
                                                  data=data, dtype=dtype,
                                                  shape=None if data is not None else (0,),
                                                  maxshape=(None,),
                                                  chunks=(CHUNKSIZE,) )
    return cls(uri, recording, dataset, metadata=metadata)

  @classmethod
  def create_from_signal(cls, recording, signal):
  #----------------------------------------------
    return cls.create(signal.uri, recording, metadata=signal.get_metavars())

  def append(self, data):
  #----------------------
    """
    :param data: Either an array or a TimeSeries of data points

    """
    if self._index is None:
      end = len(self._dset)
      self._dset.resize(end + len(data), 0)
      if isinstance(data, model.TimeSeries): self._dset[end:] = data.data
      else:                                  self._dset[end:] = data
    else: raise Exception, "Cannot append to individual signals in a group"

  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    # Compute indices into dataset
    # return self._dset[start:stop] ## But yield a sequence of TimeSeries??
    if self._index is None: return self._dest[start:stop]
    else:                   return self._dset[self._index, start:stop]

  def __getitem__(self, key):
  #--------------------------
    if self._index is None: return self._dest[key]
    else:                   return self._dset[self._index, key]


"""
/**
 * General outline:
 *
 * Open existing file loads metadata block into store *as a named graph* (we could support
 * other formats besides RDF/XML -- need say a 'format' attribute on the dataset).
 *
 * Do we replace the metadata at file close? As an option? And what? All statements
 * in the named graph.
 *
 */




    // Check if we can append to the last dataset...
    // Need to be of same type (Uniform/Non-Uniform)
    //  and
    //    if Uniform then rates match and seg.starttime = dset.endtime + tick
    //    if NonUniform then seg.starttime > dset.endtime
    //                   and there is a clock that spans seg.data

// ***     val clockid = "/clocks/" + clock.id
// ***
// ***     if (h.isDataSet(clockid)) {
// ***       val ticks = getDataSetInformation(clockid).getNumberOfElements()
// ***       }




   Dataset will be called /signals/id/N    [0...)

   Dataset has rate attribute (int) and starttime (wrt. sig start) (usecs? nanosecs??)
   Or clock attribute (string) that has id of clock.


   /clocks/clockid is a dataset
   attribute of starttime (wrt. recording) (usecs? nanosecs??)

  */
  """
