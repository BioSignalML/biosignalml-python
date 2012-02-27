######################################################
#
#  BioSignalML Project API
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


"""
This module defines classes that implement a **Block Stream** transport layer.


A *Block Stream* is a transport for blocks of data. Each block is of some *type*; it contains
both an information *header* and actual data *content*.

Blocks are sent and received as a sequence of 8-bit bytes. Using EBNF and regular
expression notation, a block is defined as::

  <block>    ::= '#' <type> <version> <header> <length> <LF> <content> '##' <checksum>? <LF>

  <type>     ::= [a-zA-Z]             /* A single, case-significant letter.        */

  <version>  ::= <INTEGER> 'V'        /* The version of the protocol.              */

  <header>   ::= <jsonlen> <json>
  <jsonlen>  ::= <INTEGER>            /* The number of bytes of JSON that follow.  */
  <json>     ::= '{' ... '}'          /* A well-formed JSON object.                */

  <length>   ::= <INTEGER>            /* The length of the content part.           */
  <content>  ::= [#x00-#xFF]*         /* A sequence of bytes.                      */

  <checksum> ::= [0-9a-fA-F]{32}      /* An optional, 32 character MD5 hex digest. */
                                      /* Includes opening '#' and closing '##'.    */
  <INTEGER> ::= [0-9]+
  <LF>      ::= #x0A

Supported block types are defined in the :class:`BlockType` class.

A block's header is a set of '(name, value)' pairs, which is sent formatted as JSON, and in
Python kept as a ``{ name: value }`` dictionary. Valid 'names' and 'values'
are specific to each block type.

"""

VERSION = 1    #: Initial version of Block Stream protocol.


import logging
import hashlib
import Queue

import numpy as np
import json


class BlockType(object):
#=======================
  '''
  Stream block types.

  The following block types are defined:
  '''

  DATA_REQ = 'd'
  """
  Request time series data from signals that is returned in :class:`SignalData` blocks.

  A data request block has no content and a header with the following fields:

    **uri** (*string*) or (*list[string]*)
      The URI of the recording or signal(s).

      A single URI can be that of a recording or signal; all URIs in a list must refer to
      signals. If the URI is of a recording then data for all signals in the recording is
      returned. Several SignalData blocks may be generated to span the requested duration;
      when the request is for multiple signals or for a recording, each signal's data will be
      in one or more separate blocks.

      REQUIRED.

    **start** (*float*)
      The time, in seconds from the start of the signal's recording, that the the first sample
      point will be at or immediately after,

      REQUIRED when multiple signals or if no *offset* is given.

    **duration** (*float*)
      The duration, in seconds, of time series data to get. A value of -1 means to get all
      starting points from the start position until the end of the time series.

      REQUIRED when multiple signals or if no *count* is given.

    **offset** (*integer*)
      The index in the signal's time series of the first sample point in the result.

      Only when requesting data from a single signal, and cannot be ussed if *start* is given.

    **count** (*integer*)
      The number of sample points to return in the result. A value of -1 means to get all
      starting points from the start position until the end of the time series.

      Only when requesting data from a single signal, and cannot be used if *duration* is given.

  The time of the first sample point in the resulting time series will not be before *start*; that
  of the last sample point will be before *start + duration*. If the signal's data finishes before
  the requested duration a shortened time series will be returned; if the period spanned in a signal
  contains discontinuous segments they will be returned in separate blocks.
  """

  DATA = 'D'
  """
  Time series data.

  The content is a segment of some signal, as an array of sample values
  optionally preceeded by an array of sample times. Sample values are either all
  a scalars or all a 1-D arrays each with the same bounds.

  A data block's header has the following fields:

    **uri** (*string*)
      The URI of the signal whose data is in the block.

      REQUIRED.

    **start** (*float*)
      The time, in seconds, from the start of the signal's recording, of the first
      sample value.

      REQUIRED.

    **offset** (*integer*)
      The index of the first sample value in the signal's time series.

      REQUIRED.

    **count** (*integer*)
      The number of sample values in the data block.

      REQUIRED.

    **dims** (*integer, default 1*)
      The number of data points in a single sample value.

      OPTIONAL.

    **dtype** (*string*)
      The numeric type of a single data point in a sample value, in the form
      '<f4' and as defined and used by numpy's array interface.

      REQUIRED.

    **rate** (*double*)
      The rate, in Hertz, of sample values.

      REQUIRED if no 'ctype' is given, otherwise MUST NOT be given.

    **ctype** (*string*)
      The numeric type of a sample time, in the form '<f4' and as defined and used
      by numpy's array interface.

      REQUIRED if no 'rate' is given, otherwise MUST NOT be given.

  The block's content consists of 'count' binary numbers of type 'ctype' (when
  'ctype' is specified), followed by 'count\*dims' binary numbers of type 'dtype'.
  """

  ERROR = 'E'
  """
  An error response.

  The block's content contains an error message as text; it's header will contain the field:

    **type** (*character*)
      The type of the request block which has resulted in an error.

  along with all fields from the original request.
  """


class StreamException(Exception):
#================================
  ''' Exceptions we can raise. '''


class Error(object):
#===================
  '''
  Error codes generated by Block Stream processing.
  '''
  NONE                 =  0    #: No errors
  UNEXPECTED_TRAILER   =  1    #: Unexpected block trailer
  MISSING_HEADER_LF    =  2    #: Missing LF on header
  MISSING_TRAILER      =  3    #: Missing block trailer
  INVALID_CHECKSUM     =  4    #: Invalid block checksum
  MISSING_TRAILER_LF   =  5    #: Missing LF on trailer
  HASH_RESERVED        =  6    #: Block type of '#' is reserved
  WRITE_EOF            =  7    #: Unexpected error when writing
  VERSION_MISMATCH     =  8    #: Block Stream has wring version
  MISSING_VERSION_FLAG =  9    #: No version delimiter
  BAD_JSON_HEADER      = 10    #: Incorrectly formatted JSON header

  @staticmethod
  def text(code):
  #--------------
    ''' Return an error code as text. '''
    return { Error.NONE:                 'No errors',
             Error.UNEXPECTED_TRAILER:   'Unexpected block trailer',
             Error.MISSING_HEADER_LF:    'Missing LF on header',
             Error.MISSING_TRAILER:      'Missing block trailer',
             Error.INVALID_CHECKSUM:     'Invalid block checksum',
             Error.MISSING_TRAILER_LF:   'Missing LF on trailer',
             Error.HASH_RESERVED:        "Block type of '#' is reserved",
             Error.WRITE_EOF:            'Unexpected error when writing',
             Error.VERSION_MISMATCH:     'Block Stream has wring version',
             Error.MISSING_VERSION_FLAG: 'No version delimiter',
             Error.BAD_JSON_HEADER:      'Incorrectly formatted JSON header',
             }.get(code, '')


class Checksum(object):
#======================
  '''
  Options for using and verifying block checksums.
  '''
  STRICT  =  1     #: Insist blocks have a checksum
  CHECK   =  2     #: Check a block's checksum when it has one
  IGNORE  =  3     #: Ignore any block checksums
  NONE    =  4     #: Blocks don't have checksums


class StreamBlock(object):
#=========================
  """
  A block exchanged using the Block Stream format.

  :type number: int
  :type type: :class:`BlockType`
  :type header: dict
  :type content: bytearray
  """

  def __init__(self, number, type, header, content):
  #-------------------------------------------------
    self.number = number
    self.type = type
    self.header = header
    self.content = content

  @classmethod
  def makeblock(cls, number, type, header, content):
  #-------------------------------------------------
    if type == BlockType.DATA:
      self = StreamDataBlock(number, header, content)
    else:
      self = cls(number, type, header, content)
    return self

  def __str__(self):
  #-----------------
    return "Block %d '%c' (%d): %s" % (self.number, self.type, len(self.content), str(self.header))

  def bytes(self, check=Checksum.NONE):
  #------------------------------------
    '''
    Return a serialisation in Block Stream format.

    :param check: Include a checksum if equal to `Checksum.STRICT`.
    :type check: :class:`Checksum`
    '''
    j = json.dumps(self.header)
    b = bytearray('#%c%dV%d%s%d\n' % (self.type, VERSION, len(j), j, len(self.content)))
    b.extend(self.content)
    b.extend('##')
    if check != Checksum.NONE:
      checksum = hashlib.md5()
      checksum.update(b)
      b.extend(checksum.hexdigest())
    b.extend('\n')
    return b


class StreamDataBlock(StreamBlock):
#==================================
  """
  A data block exchanged using the Block Stream format.

  :type number: int
  :type header: dict
  :type content: bytearray
  """
  def __init__(self, number, header, content):
  #-------------------------------------------
    StreamBlock.__init__(self, number, BlockType.DATA, header, content)

  def signaldata(self):
  #--------------------
    ''' Return a :class:`SignalData` representation of ourself. '''
    uri = self.header.get('uri', '')
    start = self.header.get('start', 0)
    count = self.header.get('count', 0)
    dims = self.header.get('dims', 1)
    dtype = self.header.get('dtype', None)
    rate = self.header.get('rate', None)
    ctype = self.header.get('ctype', None)
    dt = np.dtype(dtype)
    if rate is not None:
      if ctype is not None:
        raise StreamException("Received data stream has both a rate and clock")
      if len(self.content) != count*dims*dt.itemsize:
        raise StreamException("Received data is wrong size")
      clock = None
      if dims == 1:
        data = np.frombuffer(self.content, dtype=dt)
      else:
        data = np.reshape(np.frombuffer(self.content, dtype=dt), (count, dims))
    else:
      if ctype is None:
        raise StreamException("Received data block has no timing")
      ct = np.dtype(ctype)
      if len(self.content) != count*(ct.itemsize + dims*dt.itemsize):
        raise StreamException("Received clock and/or data is wrong size")
      datastart = count*ct.itemsize
      clock = np.frombuffer(self.content[:datastart], dtype=ct)
      if dims == 1:
        data = np.frombuffer(self.content[datastart:], dtype=dt)
      else:
        data = np.reshape(np.frombuffer(self.content[datastart:], dtype=dt), (count, dims))
    return SignalData(uri, start, data, rate, clock)


class BlockParser(object):
#=========================
  """
  Block Stream data parser.

  :param receiveQ: Either a queue on which to put complete :class:`StreamBlock`\s
    or a function to call, passing a complete `StreamBlock`.
  :type receiveQ: :class:`Queue.Queue` or function
  :param check: How any checksun is treated. Default `Checksum.CHECK`
  :type check: :class:`Checksum`
  """
  # Parser states.
  _RESET      =  0
  _TYPE       =  1
  _VERNUM     =  2
  _VERFLAG    =  3
  _HDRLEN     =  4
  _HEADER     =  5
  _DATALEN    =  6
  _HDREND     =  7
  _CONTENT    =  8
  _TRAILER    =  9
  _CHECKSUM   = 10
  _CHECKDATA  = 11
  _BLOCKEND   = 12

  def __init__(self, receiveQ, check=Checksum.CHECK):
  #--------------------------------------------------
    self._process = receiveQ.put if isinstance(receiveQ, Queue.Queue) else receiveQ
    self._check = check
    self._blockno = -1
    self._state = BlockParser._RESET
    self._error = Error.NONE

  def process(self, data):
  #-----------------------
    '''
    Parse data and put stream blocks into the receive queue.

    :param data: A chunk of data.
    :type data: bytearray
    '''
    pos = 0
    size = datalen = len(data)

    logging.debug('Process %d bytes', datalen)

    while datalen > 0:

      if   self._state == BlockParser._RESET:                   # Looking for a block
        next = data[pos:].find('#')
        if next >= 0:
          pos += (next + 1)
          datalen -= (next + 1)
          self._checksum = hashlib.md5()
          self._checksum.update('#')
          self._state = BlockParser._TYPE
        else:
          datalen = 0

      elif self._state == BlockParser._TYPE:                    # Getting block type
        self._type = chr(data[pos])
        pos += 1
        datalen -= 1
        if self._type != '#':
          self._checksum.update(self._type)
          self._blockno += 1
          self._version = 0
          self._state = BlockParser._VERNUM
        else:
          self._error = Error.UNEXPECTED_TRAILER

      elif self._state == BlockParser._VERNUM:                  # Version number
        while datalen > 0 and chr(data[pos]).isdigit():
          self._version = 10*self._version + int(chr(data[pos]))
          self._checksum.update(chr(data[pos]))
          pos += 1
          datalen -= 1
        if datalen > 0:
          self._state = BlockParser._VERFLAG

      elif self._state == BlockParser._VERFLAG:                 #
        if chr(data[pos]) == 'V':
          if self._version != VERSION:
            self._error = Error.VERSION_MISATCH
          else:
            self._checksum.update('V')
            pos += 1
            datalen -= 1
            self._length = 0
            self._state = BlockParser._HDRLEN
        else:
          self._error = Error.MISSING_VERSION_FLAG

      elif self._state == BlockParser._HDRLEN:                  # Getting header length
        while datalen > 0 and chr(data[pos]).isdigit():
          self._length = 10*self._length + int(chr(data[pos]))
          self._checksum.update(chr(data[pos]))
          pos += 1
          datalen -= 1
        if datalen > 0:
          self._jsonhdr = [ ]
          self._state = BlockParser._HEADER

      elif self._state == BlockParser._HEADER:                  # Getting header JSON
        while datalen > 0 and self._length > 0:
          self._jsonhdr.append(str(data[pos:pos+self._length]))
          self._checksum.update(str(data[pos:pos+self._length]))
          delta = min(self._length, datalen)
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0:
          try:
            self._header = json.loads(''.join(self._jsonhdr)) if len(self._jsonhdr) else { }
            self._length = 0
            self._state = BlockParser._DATALEN
          except ValueError:
            self._error = Error.BAD_JSON_HEADER
            logging.debug('JSON: %s', ''.join(self._jsonhdr))

      elif self._state == BlockParser._DATALEN:                 # Getting content length
        while datalen > 0 and chr(data[pos]).isdigit():
          self._length = 10*self._length + int(chr(data[pos]))
          self._checksum.update(chr(data[pos]))
          pos += 1
          datalen -= 1
        if datalen > 0:
          self._state = BlockParser._HDREND

      elif self._state == BlockParser._HDREND:                  # Checking header LF
        if chr(data[pos]) == '\n':
          pos += 1
          datalen -= 1
          self._checksum.update('\n')
          self._content = bytearray(self._length)
          self._chunkpos = 0
          self._state = BlockParser._CONTENT
        else:
          self._error = Error.MISSING_HEADER_LF

      elif self._state == BlockParser._CONTENT:                 # Getting content
        while datalen > 0 and self._length > 0:
          delta = min(self._length, datalen)
          self._content[self._chunkpos:self._chunkpos+delta] = data[pos:pos+delta]
          self._chunkpos += delta
          self._checksum.update(str(data[pos:pos+delta]))
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0:
          self._length = 2      # Two '#' after content
          self._state = BlockParser._TRAILER

      elif self._state == BlockParser._TRAILER:                 # Getting trailer
        if chr(data[pos]) == '#':
          self._checksum.update('#')
          pos += 1
          datalen -= 1
          self._length -= 1
          if self._length == 0: self._state = BlockParser._CHECKSUM
        else:
          self._error = Error.MISSING_TRAILER

      elif self._state == BlockParser._CHECKSUM:                # Checking for checksum
        if chr(data[pos]) != '\n' and self._check != Checksum.NONE:
          self._length = 32     # 32 checksum characters (hex digest)
          self._state = BlockParser._CHECKDATA
        else:
          self._state = BlockParser._BLOCKEND
        self._checks = [ ]

      elif self._state == BlockParser._CHECKDATA:               # Getting checksum
        while datalen > 0 and self._length > 0:
          self._checks.append(str(data[pos:pos+self._length]))
          delta = min(self._length, datalen)
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0: self._state = BlockParser._BLOCKEND

      elif self._state == BlockParser._BLOCKEND:                # Checking for final LF
        if ((self._check == Checksum.STRICT
          or self._check == Checksum.CHECK and len(self._checks))
         and ''.join(self._checks) != self._checksum.hexdigest()):
          self._error = Error.INVALID_CHECKSUM
          logging.debug('RECV: %s', ''.join(self._checks))
          logging.debug('CALC: %s', self._checksum.hexdigest())
        elif chr(data[pos]) == '\n':
          pos += 1
          datalen -= 1
          self._process(StreamBlock.makeblock(self._blockno, self._type, self._header, self._content))
          self._state = BlockParser._RESET
        else:
          self._error = Error.MISSING_TRAILER_LF

      else:                                             # Unknown state...
        self._state = BlockParser._RESET

      if self._error != Error.NONE:
        logging.error('Stream parse error: %s', Error.text(self._error))
        self._error = Error.NONE
        self._state = BlockParser._RESET


class SignalData(object):
#========================
  '''
  A segment of a :class:`~biosignalml.model.data.TimeSeries` sent or received on a :class:`BlockStream`.

  :param uri: The URI of the :class:`~biosignalml.model.Signal` which the segment is from.
  :type uri: str
  :param start: The start time of the segment, in seconds.
  :type start: double
  :param duration: The duration of the segment, in seconds.
  :type duration: double
  :param data: An one or two dimensional array of data points.
  :type data: :class:`np.array`
  :param rate: The rate, in Hertz, at which the first dimension of the data array varies.
               A value of None signifies that sampling times are in the `clock` array.
  :type rate: double
  :param clock: An one dimensional array of time points, in seconds.
  :type clock: :class:`np.array` or None
  '''
  def __init__(self, uri, start, data, rate=None, clock=None):
  #-----------------------------------------------------------
    if rate is None and clock is None:
      raise StreamException('Data must have either a rate or a clock')
    elif rate is not None and clock is not None:
      raise StreamException('Data cannot have both a rate and a clock')
    if data.ndim not in [1, 2]:
      raise StreamException('Sample points must be scalar or a 1-D array')
    if clock and clock.ndim:
      raise StreamException('Clock must be a 1-D array')
    if clock and len(clock) != len(data):
      raise StreamException('Clock and data have different lengths')
    self.uri = uri
    self.start = start
    self.data = data
    self.rate = rate
    self.clock = clock

  def __len__(self):
  #-----------------
    return len(self.data)

  def __str__(self):
  #-----------------
    return ("SignalData %s: start=%f, rate=%f\n  clock=%s\n  data=%s"
           % (self.uri, self.start, self.rate, str(self.clock), str(self.data)) )

  def streamblock(self):
  #---------------------
    ''' Return a :class:`StreamBlock` representation of the signal segment. '''
    content = bytearray()
    header = { 'uri': self.uri,
               'start': self.start,
               'count': len(self.data),
               'dtype': self.data.dtype.descr[0][1]
             }
    if self.data.ndim > 1: header['dims'] = self.data.shape[1]
    if self.rate: header['rate'] = self.rate
    if self.clock:
      header['ctype'] = self.clock.dtype.descr[0][1]
      content.extend(bytearray(self.clock))
    content.extend(bytearray(self.data))
    return StreamDataBlock(0, header, content)



class BlockStream(object):
#=========================
  """
  An `iterator` yielding :class:`SignalData` objects from a Block Stream data server.

  This class is intended to be sub-classed by a class that will establish a connection to
  the end point and then send some request.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  """
  def __init__(self, endpoint):
  #----------------------------
    self._endpoint = endpoint
    self._request = StreamBlock(0, None, { }, '')
    self._receiveQ = Queue.Queue()

  def close(self):
  #---------------
    pass

  def __iter__(self):
  #------------------
    while (True):
      block = self._receiveQ.get()
      if block is None: break
      if block.type == BlockType.ERROR:
        raise StreamError(block.content)
      yield block


class SignalDataStream(BlockStream):
#===================================
  """
  An `iterator` yielding :class:`SignalData` objects from a Block Stream data server.

  This class is intended to be sub-classed by a class that will establish a connection to
  the end point and then send a :attr:`~BlockType.DATA_REQ` request.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  :param uri: The URI of a :class:`~biosignalml.model.Recording` or of one or more
    :class:`~biosignalml.model.Signal`\s from which to get
    :class:`~biosignalml.model.data.TimeSeries` data,
  :type uri: str or list[str]
  :param start: The time, in seconds from the start of the signal's recording,
    that the first sample point will be at or immediately after,
  :type start: float or None
  :param offset: The index of the first data point. An `offset` can only be given when data from a
    single signal is requested, and cannot be specified along with `start`.
  :type offset: integer or None
  :param duration: The duration, in seconds, of signal data to return. A value
    of -1 means to get all sample points, from the starting position, of the signal(s).
  :type duration: float
  """
  def __init__(self, endpoint, uri, start=None, offset=None, duration=-1):
  #-----------------------------------------------------------------------
    BlockStream.__init__(self, endpoint)
    self._request = StreamBlock(0, BlockType.DATA_REQ, {'uri': uri, 'start': start, 'duration': duration}, '')

  def __iter__(self):
  #------------------
    for block in BlockStream.__iter__(self):
      if block.type == BlockType.DATA: yield block.signaldata()
      else:                            logging.debug('RECVD: %s', block)


class TestBlock(StreamBlock):
#============================

  @classmethod
  def block(cls, uri, start, duration):
    pass


if __name__ == '__main__':
#-------------------------

  logging.getLogger().setLevel(logging.DEBUG)

  nd = SignalData('', 10, np.ones(1),                                rate=100)
  sd = SignalData('', 10, np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), rate=100)

  print sd
  print sd.streamblock().signaldata()


  print nd
  testQ = Queue.Queue()
  bp = BlockParser(testQ, Checksum.STRICT)
  bp.process(nd.streamblock().bytes(Checksum.STRICT))

  print testQ.get(True, 10).signaldata()
