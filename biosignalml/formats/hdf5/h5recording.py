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
BioSignalML format for storing recordings in HDF5 files.

A HDF5 file contains a single Recording, with its signals, clocks, and
metadata stored as datasets. Signal datasets are either *Simple*, corresponding
one-to-one with individual Signals, or *Compound*, in which case a dataset contains
several signals all with the same timing information, as say produced by a
simulation.

Files are structured as follows::

  Path         Object    Attributes
  ----         ------    ----------
  /            Root      version
  /metadata    Dataset   mimetype
  /uris        Group
  /recording   Group     uri
    ./signal   Group
      ./0      Dataset   uri, units, gain/offset, rate/period/clock, timeunits
      ./1      Dataset   uri, units, gain/offset, rate/period/clock, timeunits
       .
    ./clock    Group
      /0       Dataset   uri, units, rate/period
       .


Objects and Attributes
======================

Root (/)
--------

The ``version`` attribute of the file is a string in the
form 'BSML m.n' --- the first five characters must be 'BSML '; this is followed
by major and minor version numbers, separated by a period ('.').

Newer major releases will always read files created by prior versions of the
software; files will always be compatible within minor releases.


/metadata dataset
-----------------

This is an optional dataset containing a RDF serialisation of metadata associated with
the recording and its signals, stored as a UTF-8 string. The ``mimetype`` attribute gives
the serialisation format, using standard mimetypes for RDF.


/uris (group)
-------------

This group has an attribute for each URI that is an attribute in the recording. It
is used to ensure URI uniqueness and to lookup datasets. The value of each attribute
is a HDF5 reference to the dataset which contains a resource's data.


/recording (group)
------------------

This group containing all signals and associated clocks that make up the Recording.
The ``uri`` attribute has the recording's URI.


/recording/signal (group)
-------------------------

Signal datasets are contained within a 'signal' group in '/recording'.

/recording/signal/N (dataset)
-----------------------------

Signal datasets are numbered, starting from '0'. A Simple dataset is one whose ``uri``
and ``units`` attributes are strings, with data points being from a single signal;
when the ``uri`` and ``units`` attributes are string arrays the dataset is Compound
and contains multiple signals, with each signal corresponding to an element of
the ``uri`` array.

A signal or group of signals can optionally have a ``gain`` and/or ``offset`` specified,
which are stored as dataset attributes. Returned signal values are obtained from the
raw data value (as read) by subtracting any offset before multiplying by any gain.

Timing for the signal(s) in a dataset is given by the mutually exclusive attributes
of ``rate``, ``period`` and ``clock``. If ``rate`` or ``period`` is given then an
optional ``timeunits`` attribute specifies the units of ``period``, with that of ``rate``
being the reciprocal; default time units are seconds. If ``clock`` is given its value
is a HDF5 reference to a dataset within the '/recording/clock' group.


/recording/clock (group)
------------------------

Any clock (i.e. timing) datasets are contained within a 'clock' group in '/recording'.

/recording/clock/N (dataset)
----------------------------

Clock datasets are numbered, starting from '0'. Attributes are ``uri`` and ``units`` with
default units of seconds. A clock can optionally have either a ``rate'' or ``period``
(= 1/rate); if so the stored value of a time point is be multiplied by the scaling factor to
obtain a value in the specified units.


Signals and Timing
==================

We do not assume that individual signal values are scalar quantities varying in time.
'time' is measured in the units given by a signal's ``timeunits`` attribute or a
clock's ``units`` attribute and could, for example, refer to a spatial position. A
signal contained in a simple dataset may be a vector or matrix quantity as well as scalar
(determined by the ``shape`` parameter when a signal is created), however all signals in a
compound signal dataset must be scalar. A clock can have scalar, vector, or
matrix 'time' values,

"""

from functools import reduce
import urllib

import h5py
import numpy as np

__all__ = [ 'H5Clock', 'H5Signal', 'H5Recording', 'IDENTIFIER' ]


MAJOR      = 1
MINOR      = 0
VERSION    = str(MAJOR) + '.' + str(MINOR)
IDENTIFIER = 'BSML ' + VERSION


COMPRESSION = 'szip'                          #: Szip gives best performance
COMPRESSION = 'gzip'                          #: Szip gives best performance

DTYPE_STRING = h5py.special_dtype(vlen=str)   #: Store strings as variable length.


class H5Clock(object):
#=====================
  """
  A clock in a HDF5 recording.

  :param dataset: A :class:`h5py.Dataset` containing the clock's data and attributes.
  """

  def __init__(self, dataset):
  #---------------------------
    self.dataset = dataset

  @property
  def name(self):
  #--------------
    """The name of the clock's dataset."""
    return self.dataset.name

  @property
  def uri(self):
  #-------------
    """The URI of the clock."""
    return self.dataset.attrs['uri']

  @property
  def times(self):
  #---------------
    """The time points of the clock."""
    t = np.asarray(self.dataset)
    attrs = self.dataset.attrs
    if   attrs.get('period'): return t*float(attrs['period'])
    elif attrs.get('rate'):   return t/float(attrs['rate'])
    else:                     return t

  @property
  def units(self):
  #---------------
    """The physical units of the clock."""
    return self.dataset.attrs.get('units')

  def __len__(self):
  #-----------------
    return self.dataset.len()

  def __getitem__(self, pos):
  #--------------------------
    """
    Return clock times by subscripting.

    :param pos: A time point index or slice specifying a range.
    :type pos: A Python slice.
    """
    t = self.dataset[pos]
    attrs = self.dataset.attrs
    if   attrs.get('period'): return t*float(attrs['period'])
    elif attrs.get('rate'):   return t/float(attrs['rate'])
    else:                     return t

  def time(self, pos):
  #-------------------
    return self[pos]


class H5Signal(object):
#======================
  """
  A single signal in a HDF5 recording.

  :param dataset: A :class:`h5py.Dataset` containing the signal's data and attributes.
  :param index: The index of the signal if the dataset is compound, otherwise None.
  """

  def __init__(self, dataset, index=None):
  #---------------------------------------
    self.dataset = dataset
    self.index = index
    self.gain = self.dataset.attrs.get('gain', 1.0)
    self.offset = self.dataset.attrs.get('offset', 0)

  @property
  def name(self):
  #--------------
    """The name of the signal's dataset."""
    return self.dataset.name

  @property
  def uri(self):
  #-------------
    """The URI of the signal."""
    uri = self.dataset.attrs['uri']
    return uri if self.index is None else uri[self.index]

  @property
  def units(self):
  #---------------
    """The physical units of the signal's data."""
    units = self.dataset.attrs['units']
    return units if self.index is None else units[self.index]

  @property
  def rate(self):
  #--------------
    """The sampling rate of the signal, or None if sampling is non-uniform."""
    attrs = self.dataset.attrs
    if   attrs.get('rate'):   return attrs['rate']
    elif attrs.get('period'): return 1.0/attrs['period']

  @property
  def period(self):
  #----------------
    """The sampling period of the signal, or None if sampling is non-uniform."""
    attrs = self.dataset.attrs
    if   attrs.get('period'): return attrs['period']
    elif attrs.get('rate'):   return 1.0/attrs['rate']

  @property
  def timeunits(self):
  #-------------------
    """The units signal timing is measured in."""
    attrs = self.dataset.attrs
    if attrs.get('clock'):
      return self.dataset.file[attrs['clock']].attrs.get('units')
    else:
      return attrs.get('timeunits')

  @property
  def clock(self):
  #---------------
    """The signal's clock dataset, or None if sampling is regular"""
    attrs = self.dataset.attrs
    if attrs.get('clock'): return H5Clock(self.dataset.file[attrs['clock']])

  def __len__(self):
  #-----------------
    return self.dataset.len()

  def __getitem__(self, pos):
  #--------------------------
    """
    Return signal data by subscripting.

    :param pos: A data point index or slice specifying a range.
    :type pos: A Python slice.
    """
    data = self.dataset[pos] if self.index is None else self.dataset[pos, self.index]
    if self.offset != 0: data -= self.offset
    if self.gain != 1.0: data = data/float(self.gain)
    return data

  def time(self, i):
  #-----------------
    """
    Get the 'time' of a data point.

    :param int i: The data point's index.
    """
    attrs = self.dataset.attrs
    if attrs.get('clock'):
      return self.dataset.file[attrs['clock']][i]
    else:
      return i * self.period


class H5Recording(object):
#=========================
  """
  Store signals as HDF5 Recordings.

  The :meth:`create` and :meth:`open` methods are intended to be used to
  create instances instead of directly using the constructor.
  """
  def __init__(self, uri, h5=None):
  #--------------------------------
    self.uri = uri
    self._h5 = h5

  def __del__(self):
  #-----------------
    self.close()


  @classmethod
  def open(cls, fname, readonly=False, **kwds):
  #--------------------------------------------
    """
    Open an existing HDF5 Recording file.

    :param str fname: The name of the file to open.
    :param bool readonly: If True don't allow updates (default = False).
    """
    try:
      if fname.startswith('file:'):
        f = urllib.urlopen(fname)
        fname = f.fp.name
        f.close()
      h5 = h5py.File(fname, 'r' if readonly else 'r+')
    except IOError, msg:
      raise IOError("Cannot open file '%s' (%s)" % (fname, msg))
    try:
      v = h5.attrs['version']
      if v[0:5] != IDENTIFIER[0:5]: raise TypeError("Not a valid BSML file")
      (m, n) = tuple([int(i) for i in v[5:].split('.')])
      if m > MAJOR:
        raise ValueError("File '%s' not compatible with version %s" % (fname, VERSION))
    except Exception:
      raise ValueError("Invalid file format")
    if not (h5.get('/uris')
        and h5.get('/recording/signal')
        and h5['recording'].attrs.get('uri')
        and h5[h5['uris'].attrs.get(h5['recording'].attrs['uri'])] == h5[h5['recording'].ref]):
      raise TypeError("'%s' is not a BioSignalML file" % fname)
    return cls(h5['recording'].attrs['uri'], h5)


  @classmethod
  def create(cls, uri, fname, replace=False, **kwds):
  #--------------------------------------------------
    """
    Create a new HDF5 Recording file.

    :param uri: The URI of the Recording contained in the file.
    :param str fname: The name of the file to create.
    :param bool replace: If True replace any existing file (default = False).
    """
    if fname.startswith('file://'): fname = fname[7:]
    try:
      h5 = h5py.File(fname, 'w' if replace else 'w-')
    except IOError, msg:
      raise IOError("Cannot create file '%s' (%s)" % (fname, msg))
    h5.attrs['version'] = IDENTIFIER
    h5.create_group('uris')
    h5.create_group('recording')
    h5.create_group('recording/signal')
    h5['recording'].attrs['uri'] = str(uri)
    h5['uris'].attrs[str(uri)] = h5['recording'].ref
    return cls(uri, h5)


  def close(self):
  #---------------
    """
    Close a HDF5 Recording file.
    """
    if self._h5:
      self._h5.close()
      self._h5 = None


  def create_signal(self, uri, units, shape=None, data=None,
                          dtype=None, gain=None, offset=None,
                          rate=None, period=None, timeunits=None, clock=None,
                          compression=COMPRESSION, **kwds):
  #---------------------------------------------------------------------------
    """
    Create a dataset for a signal or group of signals in a HDF5 recording.

    :param uri: The URI(s) of the signal(s). If ``uri`` is an iterable then the dataset
                is compound and contains several scalar signals.
    :param units: The units for the signal(s). Must be iterable and have the same number
                  of elements as ``uri`` when the dataset is compound.
    :param tuple shape: The shape of a single data point. Must be None or scalar ('()') for
                  a compound dataset. Optional.
    :param data: Initial data for the signal(s). Optional.
    :type data: :class:`numpy.ndarray` or an iterable.
    :param dtype: The datatype in which to store data points. Must be specified if
                  no ``data`` is given.
    :type dtype: :class:`numpy.dtype`
    :param float gain: If set, the signal's data values are multiplied by the ``gain`` when read. Optional.
    :param float offset: If set, ``offset`` is subtracted from a data value before any gain
                 multiplication. Optional.
    :param float rate: The frequency, as samples/time-unit, of data points.
    :param float period: The time, in time-units, between data points.
    :param timeunits: The units 'time' is measured in. Optional, default is seconds.
    :param clock: The URI of a clock dataset containing sample times. Optional.
    :return: The `H5Signal` created.

    Only one of ``rate``, ``period``, or ``clock`` can be given.

    """

    if not getattr(uri, '__iter__', None) and not getattr(units, '__iter__', None):
      if self._h5['uris'].attrs.get(str(uri)):
        raise KeyError("A signal already has URI '%s'" % uri)
      nsignals = 1
    elif (getattr(uri, '__iter__', None)
     and getattr(units, '__iter__', None)
     and len(uri) == len(units)):  # compound dataset
      for u in uri:
        if self._h5['uris'].attrs.get(str(u)):
          raise KeyError("A signal already has URI '%s'" % uri)
      nsignals = len(uri)
      if nsignals == 1:
        uri = uri[0]
        units = units[0]
    else:
      raise ValueError("'uri' and 'units' have different sizes")

    if data is not None:
      data = np.asarray(data)
    if nsignals > 1:         # compound dataset
      if shape: raise TypeError("A compound dataset can only have scalar type")
      maxshape = (None, nsignals)
      npoints = data.size/nsignals if data is not None else 0
      shape = (npoints, nsignals)
    elif shape is not None:  # simple dataset, shape of data point given
      maxshape = (None,) + shape
      elsize = reduce((lambda x, y: x * y), shape) if (len(shape) and shape[0]) else 1
      npoints = data.size/elsize if data is not None else 0
      shape = (npoints,) + shape
    elif data is not None:   # simple dataset, data determines shape
      npoints = len(data)
      maxshape = (None,) + data.shape[1:]
    else:                    # simple dataset, defaults
      npoints = 0
      shape = (0,)
      maxshape = (None,)
    if data is None and dtype is None:
      dtype = np.dtype('f8')      # Default to 64-bit float

    if rate or period:
      if (clock is not None
       or rate and period is not None
       or period and rate is not None):
        raise ValueError("Only one of 'rate', 'period', or 'clock' can be specified")
    elif clock is not None:
      if rate is not None or period is not None:
        raise ValueError("Only one of 'rate', 'period', or 'clock' can be specified")
      clocktimes = self.get_clock(clock)
      if clocktimes is None or len(clocktimes) < npoints:
        raise ValueError("Clock either doesn't exist or have sufficient times")
    else:
      raise ValueError("No timing information given")

    signo = len(self._h5['/recording/signal'])
    try:
      dset = self._h5['/recording/signal'].create_dataset(str(signo),
        data=data, shape=shape, maxshape=maxshape, dtype=dtype,
        chunks=True, compression=compression)
    except Exception, msg:
      raise RuntimeError("Cannot create signal dataset (%s)" % msg)

    if nsignals == 1:
      dset.attrs['uri'] = str(uri)
      if units is not None: dset.attrs['units'] = str(units)
      self._h5['uris'].attrs[str(uri)] = dset.ref
    else:
      dset.attrs.create('uri',   [str(u) for u in uri],   dtype=DTYPE_STRING)
      dset.attrs.create('units', [str(u) for u in units], dtype=DTYPE_STRING)
      for u in uri: self._h5['uris'].attrs[str(u)] = dset.ref
    if gain: dset.attrs['gain'] = gain
    if offset: dset.attrs['offset'] = offset
    if   rate:               dset.attrs['rate'] = float(rate)
    elif period:             dset.attrs['period'] = float(period)
    elif clock is not None:  dset.attrs['clock'] = clocktimes.dataset.ref
    if timeunits: dset.attrs['timeunits'] = timeunits
    return H5Signal(dset, None)


  def create_clock(self, uri, units=None, shape=None, times=None, dtype=None,
                                                                  rate=None, period=None,
                                                                  compression=COMPRESSION):
  #----------------------------------------------------------------------------------------
    """
    Create a clock dataset in a HDF5 recording.

    :param uri: The URI for the clock.
    :param units: The units of the clock. Optional, default is seconds.
    :param tuple shape: The shape of a single time point. Optional.
    :param times: Initial time points for the clock. Optional.
    :type times: :class:`numpy.ndarray` or an iterable.
    :param dtype: The datatype in which to store time points. Must be specified if
                  no ``times`` are given.
    :type dtype: :class:`numpy.dtype`
    :param float rate: The sample rate of time points. Optional.
    :param float period: The interval, in time units, between time points. Optional.
    :return: The `H5Clock` created.
    """
    if self._h5['uris'].attrs.get(str(uri)):
      raise KeyError("A clock already has URI '%s'" % uri)

    if times is not None:
      times = np.asarray(times)
    if shape is not None:
      maxshape = (None,) + shape
      elsize = reduce((lambda x, y: x * y), shape) if (len(shape) and shape[0]) else 1
      shape = (times.size/elsize if times is not None else 0, ) + shape
    elif times is not None:
      maxshape = list(times.shape)
      maxshape[0] = None
      maxshape = tuple(maxshape)
    else:
      shape = (0,)
      maxshape = (None,)

    self._h5['/recording'].require_group('clock')
    clockno = len(self._h5['/recording/clock'])
    try:
      dset = self._h5['/recording/clock'].create_dataset(str(clockno),
        data=times, shape=shape, maxshape=maxshape, dtype=dtype,
        chunks=True, compression=compression)
    except Exception, msg:
      raise RuntimeError("Cannot create clock dataset (%s)" % msg)

    dset.attrs['uri'] = str(uri)
    if units: dset.attrs['units'] = str(units)
    if period and rate: raise RuntimeError("Cannot specify both 'rate' and 'period' for a clock")
    if rate: dset.attrs['rate'] = float(rate)
    if period: dset.attrs['period'] = float(period)
    self._h5['uris'].attrs[str(uri)] = dset.ref
    return H5Clock(dset)


  def extend_signal(self, uri, data):
  #----------------------------------
    """
    Extend a signal dataset in a HDF5 recording.

    :param uri: The URI of the signal for a simple dataset, or of any
                signal in a compound dataset.
    :param data: Data points for the signal(s).
    :type data: :class:`numpy.ndarray` or an iterable.

    If the dataset is compound (i.e. contains several signals) then the size of the
    supplied data must be a multiple of the number of signals.
    """
    if len(data) == 0: return
    if getattr(uri, '__iter__', None) is not None:
      sig = self.get_signal(uri[0])
      if sig is None or list(sig.dataset.attrs['uri']) != list(uri):
         raise KeyError("Unknown signal set '%s'" % uri)
      dset = sig.dataset
      nsignals = len(dset.attrs['uri'])
    else:
      sig = self.get_signal(uri)
      if sig is None: raise KeyError("Unknown signal '%s'" % uri)
      dset = sig.dataset
      nsignals = 1

    if not isinstance(data, np.ndarray): data = np.array(data)

    if nsignals > 1:         # compound dataset
      npoints = data.size/nsignals
    else:                    # simple dataset
      if len(dset.shape) == 1: npoints = data.size
      else:                    npoints = data.size/reduce((lambda x, y: x * y), dset.shape[1:])
    dpoints = dset.shape[0]
    clockref = dset.attrs.get('clock')
    if clockref and self._h5[clockref].len() < (npoints+dpoints):
      raise ValueError("Clock doesn't have sufficient times")
    try:
      dset.resize(dpoints + npoints, 0)
      if nsignals > 1:         # compound dataset
        dset[dpoints:] = data.reshape((npoints, dset.shape[1]))
      else:                    # simple dataset
        dset[dpoints:] = data.reshape((npoints,) + dset.shape[1:])
    except Exception, msg:
      raise RuntimeError("Cannot extend signal dataset '%s' (%s)" % (uri, msg))


  def extend_clock(self, uri, times):
  #----------------------------------
    """
    Extend a clock dataset in a HDF5 recording.

    :param uri: The URI of the clock dataset.
    :param times: Time points with which to extend the clock.
    :type times: :class:`numpy.ndarray` or an iterable.
    """
    if len(times) == 0: return
    clock = self.get_clock(uri)
    if clock is None: raise KeyError("Unknown clock '%s'" % uri)
    dset = clock.dataset
    if not isinstance(times, np.ndarray): times = np.array(times)
    if len(dset.shape) == 1: npoints = times.size
    else:                    npoints = times.size/reduce((lambda x, y: x * y), dset.shape[1:])
    dpoints = dset.shape[0]
    try:
      dset.resize(dpoints + npoints, 0)
      dset[dpoints:] = times.reshape((npoints,) + dset.shape[1:])
    except Exception, msg:
      raise RuntimeError("Cannot extend clock dataset '%s' (%s)" % (uri, msg))


  def get_dataset_by_name(self, name):
  #-----------------------------------
    """
    Find a dataset from its name.

    :param name: The name of the dataset.
    :return: A :class:`h5py.Dataset`.
    """
    obj = self._h5.get(name)
    if isinstance(obj, h5py.Dataset): return obj


  def get_dataset(self, uri):
  #--------------------------
    """
    Find a dataset from its URI.

    :param uri: The URI of the dataset.
    :return: A :class:`h5py.Dataset` containing the resource's data, or None if
             the URI is unknown.

    If the dataset is compound it will have several URI's, one for each
    constituent signal.
    """
    ref = self._h5['uris'].attrs.get(str(uri))
    if ref: return self._h5[ref]


  def get_clock(self, uri):
  #------------------------
    """
    Find a clock dataset from its URI.

    :param uri: The URI of the clock dataset to get.
    :return: A :class:`H5Clock` or None if the URI is unknown or
             the dataset is not that for a clock.
    """
    dset = self.get_dataset(uri)
    if dset and dset.name.startswith('/recording/clock/'): return H5Clock(dset)


  def get_signal(self, uri):
  #------------------------
    """
    Find a signal from its URI.

    :param uri: The URI of the signal to get.
    :return: A :class:`H5Signal` containing the signal, or None if
             the URI is unknown or the dataset is not that for a signal.
    """
    dset = self.get_dataset(uri)
    if dset and dset.name.startswith('/recording/signal/'):
      uris = dset.attrs['uri']
      if str(uris) == str(uri): return H5Signal(dset, None)
      try:                      return H5Signal(dset, list(uris).index(str(uri)))
      except ValueError: pass
      raise KeyError("Cannot locate correct dataset for '%s'" % uri)


  def signals(self):
  #-----------------
    """
    Return all signals in the recording.

    :rtype: list of :class:`H5Signal`
    """
    uris = []
    for n in sorted(list(self._h5.get('/recording/signal'))):
      sig = self.get_dataset_by_name('/recording/signal/%s' % n)
      if sig:
        uri = sig.attrs.get('uri')
        if uri is None: pass
        elif isinstance(uri, np.ndarray): uris.extend(list(uri))
        else: uris.append(uri)
    return [ self.get_signal(u) for u in uris ]


  def clocks(self):
  #----------------
    """
    Return all clocks in the recording.

    :rtype: list of :class:`H5Clock`
    """
    uris = []
    for n in sorted(list(self._h5.get('/recording/clock'))):
      clk = self.get_dataset_by_name('/recording/clock/%s' % n)
      if clk:
        uri = clk.attrs.get('uri')
        if uri is None: pass
        else: uris.append(uri)
    return [ self.get_clock(u) for u in uris ]


  def store_metadata(self, metadata, mimetype):
  #--------------------------------------------
    """
    Store metadata in the HDF5 recording.

    :param metadata: RDF serialised as a string.
    :type metadata: str or unicode
    :param mimetype: A mimetype string for the RDF format used.

    Metadata is encoded as UTF-8 when stored.
    """
    if self._h5.get('/metadata'): del self._h5['/metadata']
    md = self._h5.create_dataset('/metadata', data=metadata.encode('utf-8'))
    md.attrs['mimetype'] = mimetype

  def get_metadata(self):
  #----------------------
    """
    Get metadata from the HDF5 recording.

    :return: A 2-tuple of retrieved metadata and mimetype, or
             (None, None) if the recording has no '/metadata' dataset.
    :rtype: tuple(unicode, str)
    """
    if self._h5.get('/metadata'):
      md = self._h5['/metadata']
      return (md[()].decode('utf-8'), md.attrs.get('mimetype'))
    else:
      return (None, None)


if __name__ == '__main__':
#=========================

  f = H5Recording.create('/some/uri', 'test.h5', True)
  f.store_metadata('metadata string', 'mimetype')
  f.close()

  g = H5Recording.open('test.h5')

  g.create_signal('a signal URI', 'mV', data=[1, 2, 3], rate=10)
  
  g.create_signal('2d signal', 'mV', data=[1, 2, 3, 4], shape=(2,), rate=100)

  g.create_signal(['URI1', 'URI2'], ['mA', 'mV'], data=[1, 2, 3, 4], period=0.001)

  g.create_clock('clock URI', times=[1, 2, 3, 4, 5])
  g.create_signal('another signal URI', 'mV', data=[1, 2, 1], clock='clock URI')

  g.create_clock('2d clock', times=[1, 2, 3, 4, 5, 6], shape=(2,))

  g.extend_signal('2d signal', [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ])

  g.extend_clock('clock URI', [ 1, 2, 4, 5, 6, 7, 8, 9, ])
  g.extend_signal('another signal URI', [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ])

  print g.get_metadata()

  g.close()


"""
Scalar signal:
  [ 1, 2, 1, 2, 3, 2, ... ]
  shape    = (   6, )
  maxshape = (None, )

Signal of 3-d positions:
  [ [1, 2, 1], [2, 3, 1], [2, 1, 2], [3, 1, 2], [1, 2, 3], ... ]
  shape    = (   5, 3)
  maxshape = (None, 3)

Compound dataset with 4 scalar signals:
  [ [ 1, 2, 1, 2, 3, ... ],
    [ 1, 2, 1, 2, 3, ... ],
    [ 1, 2, 1, 2, 3, ... ],
    [ 1, 2, 1, 2, 3, ... ] ]
  shape    = (4,    5)
  maxshape = (4, None)

Compound dataset with 5 2-d signals:
  [ [ [1, 2], [2, 2], [3, 1], ... ],
    [ [1, 2], [2, 2], [3, 1], ... ],
    [ [1, 2], [2, 2], [3, 1], ... ],
    [ [1, 2], [2, 2], [3, 1], ... ],
    [ [1, 2], [2, 2], [3, 1], ... ] ]
  shape    = (5,    3, 2)
  maxshape = (5, None, 2)
"""
