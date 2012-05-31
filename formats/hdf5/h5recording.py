"""
BioSignalML format for storing recordings in HDF5 files.

A HDF5 file contains a single Recording, with its signals, clocks, and
metadata storered as datasets. Signal datasets are either *Simple*, corresponding
one-to-one with individual Signals, or *Compound*, in which case a dataset contains
several signals all with the same timing information, as say produced by a
simulation.

Files are structured as follows::

  Path         Object    Attributes
  ----         ------    ----------
  /            Root      version
  /metadata    Dataset   format
  /uris        Group
  /recording   Group     uri
    ./signal   Group
      ./0      Dataset   uri, units, rate/period/clock, timeunits
      ./1      Dataset   uri, units, rate/period/clock, timeunits
       .
    ./clock    Group
      /0       Dataset   uri, units
       .


Objects and Attributes
======================

Root (/)
--------

The ``version`` attribute of the file is a string in the
form 'BSML m.n' --- the first five characters must be 'BSML '; this is followed
by major and minor version numbers, separated by a period ('.').

Newer major releases will always read files created by prior versions of the
software; files will always be compatible withhin minor releases.


/metadata (dataset)
-------------------

This is an optional dataset containing a RDF serialisation of metadata associated with
the recording and its signals. The ``format`` attribute gives the serialisation format,
using standard mimetypes for RDF.


/uris (group)
-------------

This group has an attribute for each URI that is an attribute in the recording. It
is used to ensure URI uniqeness and to lookup datasets. The value of each attribute
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

Timing for the signal(s) in a dataset is given by the mutually exclusive attributes
of ``rate``, ``period`` and ``clock``. If ``rate`` or ``period`` is given then an
optional ``timeunits`` attribute specifies the units of ``period``, with that of ``rate``
being the reciprocal; default units are seconds. If ``clock`` is given its value
is a HDF5 reference to a dataset within the '/recording/clock' group.


/recording/clock (group)
------------------------

Any clock (i.e. timing) datasets are contained within a 'clock' group in '/recording'.

/recording/clock/N (dataset)
----------------------------

Clock datasets are numbered, starting from '0'. Attributes are ``uri`` and ``units``;
default units are seconds.


Signals and Timing
==================

We do not assume that individual signal values are scalar quantities varying in time.
'time' is measured in whatever units are given for a signal's ``timeunits`` attribute or a
clock's ``units`` attribute and could for example refer to a spatial position. A signal
value in a simple dataset may be a vector or matrix quantity, as determined by the
``shape`` parameter when a signal is created, as well as scalar; all signals in a
compound signal dataset must be scalar. Similarly a clock can have sclar, vector, or
matrix 'time' values,

"""

from functools import reduce

import h5py
import numpy as np


MAJOR      = 1
MINOR      = 0
VERSION    = str(MAJOR) + '.' + str(MINOR)
IDENTIFIER = 'BSML ' + VERSION


COMPRESSION = 'gzip'

DTYPE_STRING = h5py.special_dtype(vlen=str)   #: Store strings as variable length.


class H5Recording(object):
#=========================
  """
  Store signals as HDF5 Recordings.

  The `create` and `open` class methods are intended to be used instead
  of directly constructing instances.
  """
  def __init__(self, uri, fname, h5=None, **kwds):
  #-----------------------------------------------
    self._h5 = h5

  def __del__(self):
  #-----------------
    self.close()


  @classmethod
  def open(cls, fname, readonly=False, **kwds):
  #--------------------------------------------
    """
    Open an existing HDF5 Recording file.

    :param fname: The name of the file to open.
    :type fname: str
    :param readonly: If True don't allow updates (default = False).
    :param readonly: bool
    """
    try:
      h5 = h5py.File(fname, 'r' if readonly else 'r+')
    except IOError, msg:
      raise IOError("Cannot open file '%s' (%s)", (fname, msg))
    try:
      v = h5.attrs['version']
      if v[0:5] != IDENTIFIER[0:5]: raise TypeError
      (m, n) = tuple([int(i) for i in v[5:].split('.')])
      if m > MAJOR: raise ValueError
    except Exception:
      raise ValueError("File '%s' not compatible with version %s" % (fname, VERSION))
    if (not h5.get('/uris')
     or not h5.get('/recording/signal')
     or not h5['recording'].attrs.get('uri')):
      raise TypeError("'%s' is not a BioSignalML file" % fname)
    return cls(h5['recording'].attrs['uri'], fname, h5, **kwds)


  @classmethod
  def create(cls, uri, fname, replace=False, **kwds):
  #--------------------------------------------------
    """
    Create a new HDF5 Recording file.

    :param uri: The URI of the Recording contained in the file.
    :param fname: The name of the file to create.
    :type fname: str
    :param replace: If True replace any existing file (default = False).
    :param replace: bool
    """
    try:
      h5 = h5py.File(fname, 'w' if replace else 'w-')
    except IOError, msg:
      raise IOError("Cannot create file '%s' (%s)", (fname, msg))
    h5.attrs['version'] = IDENTIFIER
    h5.create_group('uris')
    h5.create_group('recording')
    h5.create_group('recording/signal')
    h5['recording'].attrs['uri'] = str(uri)
    h5['uris'].attrs[str(uri)] = h5.ref
    return cls(uri, fname, h5, **kwds)


  def close(self):
  #---------------
    """
    Close a HDF5 Recording file.
    """
    if self._h5:
      self._h5.close()
      self._h5 = None



  def create_signal(self, uri, units, shape=None, data=None, dtype=None,
                          rate=None, period=None, timeunits=None, clock=None):
  #------------------------------------------------------------------------
    """
    Create a dataset for a signal or group of signals in a HDF5 recording.

    :param uri: The URI(s) of the signal(s). If ``uri`` is an iterable then the dataset
                is compound and contains several scalar signals.
    :param units: The units for the signal(s). Must be iterable and have the same number
                  of elements as ``uri`` when the dataset is compound.
    :param shape: The shape of a single data point. Must be None or scalar ('()') for
                  a compound dataset. Optional.
    :type shape: tuple
    :param data: Initial data for the signal(s). Optional.
    :type data: :class:`numpy.ndarray` or an iterable.
    :param dtype: The datatype in which to store data points. Must be specified if
                  no ``data`` is given.
    :type dtype: :class:`numpy.dtype`
    :param rate: The frequency, as samples/time-unit, of data points.
    :type rate: float
    :param period: The time, in time-units, between data points.
    :type period: float
    :param timeunits: The units 'time' is measured in. Optional, default is seconds.
    :param clock: The URI of a clock dataset containing sample times. Optional.
    :return: The name of the signal dataset created.
    :rtype: str

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

    if data and not isinstance(data, np.ndarray):
      data = np.array(data)
    if nsignals > 1:         # compound dataset
      if shape: raise TypeError("A compound dataset can only have scalar type")
      maxshape = (nsignals, None)
      npoints = data.size/nsignals if data is not None else 0
      shape = (nsignals, npoints)
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

    if rate or period:
      if (clock is not None
       or rate and period is not None
       or period and rate is not None):
        raise ValueError("Only one of 'rate', 'period', or 'clock' can be specified")
    elif clock is not None:
      if rate is not None or period is not None:
        raise ValueError("Only one of 'rate', 'period', or 'clock' can be specified")
      clocktimes = self._h5.get(clock)
      if clocktimes is None or clocktimes.len() < npoints:
        raise ValueError("Clock either doesn't exist or have sufficient times")
    else:
      raise ValueError("No timing information given")

    signo = len(self._h5['/recording/signal'])
    try:
      dset = self._h5['/recording/signal'].create_dataset(str(signo),
        data=data, shape=shape, maxshape=maxshape, dtype=dtype,
        chunks=True, compression=COMPRESSION)
    except Exception, msg:
      raise RuntimeError("Cannot create signal dataset (%s)" % msg)

    if nsignals == 1:
      dset.attrs['uri'] = str(uri)
      dset.attrs['units'] = str(units)
      self._h5['uris'].attrs[str(uri)] = dset.ref
    else:
      dset.attrs.create('uri',   [str(u) for u in uri],   dtype=DTYPE_STRING)
      dset.attrs.create('units', [str(u) for u in units], dtype=DTYPE_STRING)
      for u in uri: self._h5['uris'].attrs[str(u)] = dset.ref
    if   rate:               dset.attrs['rate'] = rate
    elif period:             dset.attrs['period'] = period
    elif clock is not None:  dset.attrs['clock'] = clocktimes.ref
    if timeunits: dset.attrs['timeunits'] = timeunits
    return dset.name


  def create_clock(self, uri, units=None, shape=None, times=None, dtype=None):
  #---------------------------------------------------------------------------
    """
    Create a clock dataset in a HDF5 recording.

    :param uri: The URI for the clock.
    :param units: The units of the clock. Optional, default is seconds.
    :param shape: The shape of a single time point. Optional.
    :type shape: tuple
    :param times: Initial time points for the clock. Optional.
    :type times: :class:`numpy.ndarray` or an iterable.
    :param dtype: The datatype in which to store time points. Must be specified if
                  no ``times`` are given.
    :type dtype: :class:`numpy.dtype`
    :return: The name of the clock dataset created.
    :rtype: str
    """
    if self._h5['uris'].attrs.get(str(uri)):
      raise KeyError("A clock already has URI '%s'" % uri)
    if times and not isinstance(times, np.ndarray):
      times = np.array(times)
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
        chunks=True, compression=COMPRESSION)
    except Exception, msg:
      raise RuntimeError("Cannot create clock dataset (%s)" % msg)

    dset.attrs['uri'] = str(uri)
    if units: dset.attrs['units'] = str(units)
    self._h5['uris'].attrs[str(uri)] = dset.ref
    return dset.name


  def extend_signal(self, name, data):
  #-----------------------------------
    """
    Extend a signal dataset in a HDF5 recording.

    :param name: The name of the dataset.
    :type name: str
    :param data: Data points for the signal(s).
    :type data: :class:`numpy.ndarray` or an iterable.

    If the dataset is compound (i.e. contains several signals) then the size of the
    supplied data must be a multiple of the number of signals.
    """
    dset = self._h5.get(name)
    if dset is None: raise KeyError("Unknown signal '%s'" % name)
    nsignals = len(dset.attrs['uri']) if dset.attrs['uri'].shape else 1
    if not isinstance(data, np.ndarray): data = np.array(data)

    if nsignals > 1:         # compound dataset
      npoints = data.size/nsignals
      dpoints = dset.shape[1]
    else:                    # simple dataset
      if len(dset.shape) == 1: npoints = data.size
      else:                    npoints = data.size/reduce((lambda x, y: x * y), dset.shape[1:])
      dpoints = dset.len()
    clock = dset.attrs.get('clock')
    if clock and clock.len() < npoints:
      raise ValueError("Clock doesn't have sufficient times")
    try:
      if nsignals > 1:         # compound dataset
        dset.resize(dpoints + npoints, 1)
        dset[..., dpoints:] = data.reshape((dset.shape[0], npoints))
      else:                    # simple dataset
        dset.resize(dpoints + npoints, 0)
        dset[dpoints:] = data.reshape((npoints,) + dset.shape[1:])
    except Exception, msg:
      raise RuntimeError("Cannot extend signal dataset '%s' (%s)" % (name, msg))


  def extend_clock(self, name, times):
  #-----------------------------------
    """
    Extend a clock dataset in a HDF5 recording.

    :param name: The name of the dataset.
    :type name: str
    :param times: Time points for the clock.
    :type times: :class:`numpy.ndarray` or an iterable.
    """
    dset = self._h5.get(name)
    if dset is None: raise KeyError("Unknown clock '%s'" % name)
    if not isinstance(times, np.ndarray): times = np.array(times)
    if len(dset.shape) == 1: npoints = times.size
    else:                    npoints = times.size/reduce((lambda x, y: x * y), dset.shape[1:])
    dpoints = dset.len()
    try:
      dset.resize(dpoints + npoints, 0)
      dset[dpoints:] = times.reshape((npoints,) + dset.shape[1:])
    except Exception, msg:
      raise RuntimeError("Cannot extend clock dataset '%s' (%s)" % (name, msg))



if __name__ == '__main__':
#=========================

  f = H5Recording.create('/some/uri', 'test.h5', True)
  f.close()

  g = H5Recording.open('test.h5')


  g.create_signal('a signal URI', 'mV', data=[1, 2, 3], rate=10)
  
  s2 = g.create_signal('2d signal', 'mV', data=[1, 2, 3, 4], shape=(2,), rate=100)

  g.create_signal(['URI1', 'URI2'], ['mA', 'mV'], data=[1, 2, 3, 4], period=0.001)

  c = g.create_clock('clock URI', times=[1, 2, 3, 4, 5])
  g.create_signal('another signal URI', 'mV', data=[1, 2, 1], clock=c)

  g.create_clock('2d clock', times=[1, 2, 3, 4, 5, 6], shape=(2,))

  g.extend_signal(s2, [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ])

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
