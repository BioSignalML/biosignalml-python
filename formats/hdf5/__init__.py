######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: c1bb582 on Tue May 1 10:48:29 2012 +1200 by Dave Brooks $
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


from biosignalml import BSML, UniformSignal
from biosignalml.data import TimeSeries, UniformTimeSeries

from biosignalml.formats import BSMLRecording, BSMLSignal


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


def _set_attribute(obj, hdf5, attr, value):
#------------------------------------------
  if (value is not None and (value != ''
         or not isinstance(value, str) and not isinstance(value, unicode))):
    ##logging.debug("Attr %s: '%s' to '%s'", hdf5, attr, value)
    object.__setattr__(obj, attr, value)
    hdf5.attrs[attr] = value if isinstance(value, Number) else str(value)
  elif attr in hdf5.attrs:
    del hdf5.attrs[attr]



class HDF5Signal(BSMLSignal):
#============================

  def __init__(self, uri, metadata=None, **kwds):
  #----------------------------------------------
    BSMLSignal.__init__(self, uri, metadata=metadata, **kwds)
    self._dsetname = None
    self._dset = None
    #if index is None: self._dset.attrs['uri'] = str(self.uri)
    #_set_clock(self._dset, attr, value)
    #_del_clock(self._dset, attr)


  def _name(self):
  #---------------
    return _make_name(self.recording.uri, self.uri)

  def open_dataset(self):
  #----------------------
    if self._dset is None:
      self._dset = self.recording.get_dataset(self._name())
      assert self._dset.attrs['uri'] == str(self.uri)
    #try:
    #  index = self.recording.get_dataset('uris').index(str(self.uri))
    #except ValueError:
    #  raise ValueError, 'Signal %s is not in Recording' % str(uri)

  def create_dataset(self, data=None, dtype=np.dtype('f')):
  #--------------------------------------------------------
    if self._dset is None:
      name = self._name()
      try:
        self.open_dataset()
      except KeyError:
        self._dset = self.recording.create_dataset(self._name(),
                                                   data=data,
                                                   dtype=None if data is not None else dtype,
                                                   shape=None if data is not None else (0,),
                                                   maxshape=(None,), chunks=(CHUNKSIZE,) )
        self._dset.attrs['uri']  = str(self.uri)
        self._dset.attrs['rate'] = self.rate   ## Or clock
        #if attr in ['clock', 'rate']:
        #  if value: hdf5.attrs[attr] = value if isinstance(value, Number) else str(value)
    ## Set datatype by first append... In fact only create dataset then...

  @classmethod
  def create_from_signal(cls, recording, signal):
  #----------------------------------------------
    return cls.create(signal.uri, recording, metadata=signal.get_metavars())

  def append(self, data):
  #----------------------
    """
    :param data: Either an array or a TimeSeries of data points

    """
    if data is None or len(data) == 0: return
    if isinstance(data, TimeSeries):
      if isinstance(data, UniformTimeSeries):
        if data.rate != self.rate: raise ValueError, "Data rate different from signal's"
      #else:                                  ## check clock
      data = data.data
    if self._dset is None:
      self.create_dataset(data)
    else:
      end = len(self._dset)
      self._dset.resize(end + len(data), 0)
      self._dset[end:] = data


  def read(self, interval=None, segment=None, duration=None, points=0):
  #--------------------------------------------------------------------
    # Compute indices into dataset
    # return self._dset[start:stop] ## But yield a sequence of TimeSeries??
    self.open()
    return self._dest[start:stop]
    #if self._index is None: return self._dest[start:stop]
    #else:                   return self._dset[self._index, start:stop]

  def __getitem__(self, key):
  #--------------------------
    if self._index is None: return self._dest[key]
    else:                   return self._dset[self._index, key]



class HDF5Recording(BSMLRecording):
#==================================

  FORMAT = BSML.BSML_HDF5
  MIMETYPE = 'application/x-bsml'
  EXTENSIONS = [ 'h5', 'hdf', 'hdf5' ]
  SignalClass = HDF5Signal

  def __init__(self, uri, fname=None, metadata=None, **kwds):
  #----------------------------------------------------------
    BSMLRecording.__init__(self, uri, fname, metadata=metadata, **kwds)
    self._file = None
    self._recording = None

  def _openfile(self, fname, mode='r'):
  #------------------------------------
    # check filename extension and add '.h5' or '.hdf5'  ???
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
    if self._file is not None:
      self._file.close()
      self._file = None


  @classmethod
  def open(cls, fname, uri=None, mode='r', **kwds):
  #------------------------------------------------
    self = cls(uri, fname=fname, **kwds)
    self._openfile(fname, mode=mode)
    return self
    # If multiple recordings per file then can we add extra recordings?
    # With no extension of existing recordings??
    # read/parse metadata and add to self._graph (self._model ??)
    # and then add all Signals to Recording...


  @classmethod
  def create(cls, fname, uri=None, **kwds):
  #----------------------------------------
    return cls.open(fname, uri=uri, mode='w', **kwds)


  ## create_from_recording sets source to recording.uri? or recording.source??
##  @classmethod
##  def create_from_recording(cls, recording, fname):
##  #------------------------------------------------
##    return cls.create(fname, uri=recording.uri, metadata=recording.get_metavars())


  def create_dataset(self, name, **kwds):
  #--------------------------------------
    return self._recording.create_dataset(name, **kwds)

  def get_dataset(self, name):
  #---------------------------
    return self._recording[name]

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
    self.create_dataset('uris', data=[str(u) for u in uris], dtype=h5py.new_vlen(str))
    dataset = self.create_dataset('data', dtype=dtype,
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




if __name__ == '__main__':
#=========================


  hdf5 = HDF5Recording.create('test.h5', 'http://example.org/test/bsml')

  #sig = hdf5.new_signal(UniformSignal, id='1', units='mV', rate=1000)

  sig = hdf5.new_signal(id='1', units='mV', rate=1000)
  data = UniformTimeSeries(np.sin(np.linspace(0, 4*np.pi, 201)), rate=sig.rate)
  sig.append(data)
  sig.append(data.data[1:])

  sig = hdf5.new_signal(id='2', units='mV', rate=100.0)
  sig.append(UniformTimeSeries(np.arange(0, sig.rate+1, dtype=np.dtype('b')), rate=sig.rate))

  hdf5.close()

"""


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

"""
