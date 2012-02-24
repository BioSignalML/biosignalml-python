######################################################
#
#  BioSignalML Project API
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################
'''
Send and receive BioSignalML data using Web Sockets.
'''

import hashlib
import Queue
from collections import namedtuple
import logging

import json
import numpy as np
import ws4py.client.threadedclient


class Error(object):
#===================
  '''
  Error codes.
  '''
  NONE               = 0    #: No errors                  
  UNEXPECTED_TRAILER = 1    #: Unexpected block trailer   
  MISSING_HEADER_LF  = 2    #: Missing LF on header       
  MISSING_TRAILER    = 3    #: Missing block trailer      
  INVALID_CHECKSUM   = 4    #: Invalid block checksum     
  MISSING_TRAILER_LF = 5    #: Missing LF on trailer      
  HASH_RESERVED      = 6    #: Block type of '#' is reserved
  WRITE_EOF          = 7    #: Unexpected error when writing

  @staticmethod
  def text(code):
  #--------------
    ''' Return an error code as text. '''
    return { Error.NONE:               'No errors',
             Error.UNEXPECTED_TRAILER: 'Unexpected block trailer',
             Error.MISSING_HEADER_LF:  'Missing LF on header',
             Error.MISSING_TRAILER:    'Missing block trailer',
             Error.INVALID_CHECKSUM:   'Invalid block checksum',
             Error.MISSING_TRAILER_LF: 'Missing LF on trailer',
             Error.HASH_RESERVED:      "Block type of '#' is reserved",
             Error.WRITE_EOF:          'Unexpected error when writing',
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


StreamBlock = namedtuple('StreamBlock', 'number, type, header, content')
''' A block exchanged using Simple Stream Format. '''


class BlockParser(object):
#=========================
  """
  Simple Stream Format data parser.

  :param receiveQ: A queue on which to put complete `StreamBlock`'s
  :type receiveQ: :class:`Queue.Queue`
  :param check: How any checksun is treated. Default `Checksum.CHECK`
  :type check: :class:`Checksum`
  """
  # Parser states.
  RESET      =  0
  TYPE       =  1
  HDRLEN     =  2
  HEADER     =  3
  HDREND     =  4
  CONTENT    =  5
  TRAILER    =  6
  CHECKSUM   =  7
  CHECKDATA  =  8
  BLOCKEND   =  9

  def __init__(self, receiveQ, check=Checksum.CHECK):
  #--------------------------------------------------
    self._receiveQ = receiveQ
    self._check = check
    self._blockno = -1
    self._state = BlockParser.RESET    #: The parser's state.
    ''' The block currently being received '''
    self._error = Error.NONE     #: Set when there is an error

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

      if   self._state == BlockParser.RESET:                   # Looking for a block
        next = data[pos:].find('#')
        if next >= 0:
          pos += (next + 1)
          datalen -= (next + 1)
          self._checksum = hashlib.md5()
          self._checksum.update('#')
          self._state = BlockParser.TYPE
        else:
          datalen = 0

      elif self._state == BlockParser.TYPE:                    # Getting block type
        self._type = chr(data[pos])
        pos += 1
        datalen -= 1
        if self._type != '#':
          self._checksum.update(self._type)
          self._blockno += 1
          self._length = 0
          self._state = BlockParser.HDRLEN
        else:
          self._error = Error.UNEXPECTED_TRAILER

      elif self._state == BlockParser.HDRLEN:                  # Getting header length
        while datalen > 0 and chr(data[pos]).isdigit():
          self._length = 10*self._length + int(chr(data[pos]))
          self._checksum.update(chr(data[pos]))
          pos += 1
          datalen -= 1
        if datalen > 0:
          self._jsonhdr = [ ]
          self._state = BlockParser.HEADER

      elif self._state == BlockParser.HEADER:                  # Getting header JSON
        while datalen > 0 and self._length > 0:
          self._jsonhdr.append(str(data[pos:pos+self._length]))
          self._checksum.update(str(data[pos:pos+self._length]))
          delta = min(self._length, datalen)
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0:
          self._header = json.loads(''.join(self._jsonhdr)) if len(self._jsonhdr) else { }
          self._state = BlockParser.HDREND

      elif self._state == BlockParser.HDREND:                  # Checking header LF
        if chr(data[pos]) == '\n':
          pos += 1
          datalen -= 1
          self._checksum.update('\n')
          self._length = self._header.pop('length', 0)
          self._content = bytearray(self._length)
          self._chunkpos = 0
          self._state = BlockParser.CONTENT
        else:
          self._error = Error.MISSING_HEADER_LF

      elif self._state == BlockParser.CONTENT:                 # Getting content
        while datalen > 0 and self._length > 0:
          delta = min(self._length, datalen)
          self._content[self._chunkpos:self._chunkpos+delta] = data[pos:pos+delta]
          self._chunkpos += delta
          self._checksum.update(str(data[pos:pos+delta]))
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0:
          self._length = 2
          self._state = BlockParser.TRAILER

      elif self._state == BlockParser.TRAILER:                 # Getting trailer
        if chr(data[pos]) == '#':
          pos += 1
          datalen -= 1
          self._length -= 1
          if self._length == 0: self._state = BlockParser.CHECKSUM
        else:
          self._error = Error.MISSING_TRAILER

      elif self._state == BlockParser.CHECKSUM:                # Checking for checksum
        if chr(data[pos]) != '\n' and self._check != Checksum.NONE:
          self._length = 32
          self._state = BlockParser.CHECKDATA
        else:
          self._state = BlockParser.BLOCKEND
        self._checks = [ ]

      elif self._state == BlockParser.CHECKDATA:               # Getting checksum
        while datalen > 0 and self._length > 0:
          self._checks.append(str(data[pos:pos+self._length]))
          delta = min(self._length, datalen)
          pos += delta
          datalen -= delta
          self._length -= delta
        if self._length == 0: self._state = BlockParser.BLOCKEND

      elif self._state == BlockParser.BLOCKEND:                # Checking for final LF
        if ((self._check == Checksum.STRICT
          or self._check == Checksum.CHECK and len(self._checks))
         and ''.join(self._checks) != self._checksum.hexdigest()):
          self._error = Error.INVALID_CHECKSUM
        elif chr(data[pos]) == '\n':
          pos += 1
          datalen -= 1
          self._receiveQ.put(StreamBlock(self._blockno, self._type, self._header, self._content))
          self._state = BlockParser.RESET
        else:
          self._error = Error.MISSING_TRAILER_LF

      else:                                             # Unknown state...
        self._state = BlockParser.RESET

      if self._error != Error.NONE:
        logging.error('Stream parse error: %s', Error.text(self._error))
        self._error = Error.NONE
        self._state = BlockParser.RESET


class WebSocketReadStream(ws4py.client.threadedclient.WebSocketClient):
#======================================================================
  """
  A web socket connection.
  
  We send a data request when the connection is established and then then parse received data.
  Stream blocks found are put on to `receiveQ`.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  :param request: Text to end as a data request.
  :type request: str
  :param receiveQ: A queue on which to put complete `StreamBlock`'s. `None` is
   sent when the stream has finished.
  :type receiveQ: :class:`Queue.Queue`
  :param check: How any checksun is treated. Default `Checksum.CHECK`
  :type check: :class:`Checksum`
  """
  def __init__(self, endpoint, request, receiveQ, check=Checksum.CHECK, **kwds):
  #-----------------------------------------------------------------------------
    ws4py.client.threadedclient.WebSocketClient.__init__(self, endpoint, **kwds)
    self._request = request
    self._receiveQ = receiveQ
    self._parser = BlockParser(receiveQ, check=check)

  def opened(self):
  #----------------
    self.send(self._request)

  def closed(self, code, reason=None):
  #-----------------------------------
    self._receiveQ.put(None)
      
  def received_message(self, msg):
  #--------------------------------
    self._parser.process(msg.data)


class StreamData(object):
#========================
  '''
  A segment of a :class:`biosignalml.model.data.TimeSeries` sent or received on a :class:`WebSocketReadStream`.

  :param start: The start time of the segment, in seconds.
  :type start: double
  :param duration: The duration of the segment, in seconds.
  :type duration: double
  :param data: An one or two dimensional array of data points.
  :type data: :class:`np.array`
  :param rate: The rate, in Hertz, at which the first dimension of the data array varies.
               A value of 0 signifies that sampling times are in the `clock` array.
  :type rate: double
  :param clock: An one dimensional array of time points, in seconds.
  :type clock: :class:`np.array` or None
  '''
  def __init__(self, start, duration, data, rate=0, clock=None):
  #-------------------------------------------------------------
    if rate == 0 and clock is None:
      raise StreamException('Data must have either a rate or a clock')
    elif rate != 0 and clock is not None:
      raise StreamException('Data cannot have both a rate and a clock')
    self.start = start
    self.duration = duration
    self.data = data
    self.rate = rate
    self.clock = clock

  def __str__(self):
  #-----------------
    return ("StreamData: start=%f, duration=%f, rate=%f\n  clock=%s\n  data=%s"
           % (self.start, self.duration, self.rate, str(self.clock), str(self.data)) )


class StreamDataReader(object):
#==============================
  """
  An `iterator` yielding :class:`StreamData` objects from a data stream server.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  :param uri: The URI of a :class:`biosignalml.model.Recording` or :class:`biosignalml.model.Signal`
    from which to get :class:`biosignalml.model.data.TimeSeries` data,
  :type uri: str
  :param start: The time, in seconds, that the first data point will be at or immediately after,
  :type start: float
  :param duration: The maximum duration, in seconds, of the :class:`TimeSeries` returned.
  :type duration: float
  """
  def __init__(self, endpoint, uri, start, duration):
  #--------------------------------------------------
    request = "{'uri': '%s', 'start': %f, 'duration': %f}" % (uri, start, duration)
    self._receiveQ = Queue.Queue()
    try:
      self._ws = WebSocketReadStream(endpoint, request, self._receiveQ, protocols=['biosignalml-ssf'])
      self._ws.connect()
    except Exception, msg:
      logging.error('Unable to connect to WebSocket: %s', msg)
      raise IOError('Cannot open StreamDataReader')

  def close(self):
  #---------------
    self._ws.close()

  def __iter__(self):
  #------------------
    block = self._receiveQ.get()
    if block is not None:
      # Check type == STREAM.TYPE_DATA  ('D')
      # Use header fields to get start, duration, rate
      # Use header clock/data kind fields to create np.arrays for clock and data
      yield 'block %d: %c %s (%d bytes)' % (block.number, block.type, str(block.header), len(block.content))
      #yield StreamData(...)



if __name__ == '__main__':
#=========================

  import sys

  logging.getLogger().setLevel(logging.DEBUG)

  if len(sys.argv) < 5:
    print 'Usage: %s endpoint uri start duration' % sys.argv[0]
    sys.exit(1)

  for d in StreamDataReader(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) ):
    print d
