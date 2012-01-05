"""
Send and receive blocks of binary data over a file-like object.

A block consists of:

* a start byte (0x7E).
* a byte containg the block type.
* a sequence number field (one to four bytes).
* a length field, with the content's length (one to four bytes).
* the block's content.
* an end byte (0x0A).
"""

######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################


import threading, Queue
import logging
import struct
import os, sys, fcntl
from numbers import Number


# Block types:
BLOCK_INFO  = 'I'
BLOCK_DATA  = 'D'
BLOCK_META  = 'M'
BLOCK_EVENT = 'E'

# Block delimiters:
BLOCK_START = '\x7E'
BLOCK_END   = '\x0A'

READ_BLOCK_SIZE = 4096


class BlockError(Exception):
#===========================#
  pass


def pack_number(n):
#=================
  """
  Variable length integer encoding.

  * An integer is sent encoded into 1, 2 or 4 bytes.
  * If the number is less than 128 then it is sent as a single byte.
  * If the number is between 128 and 16383 (= 2^14 - 1) inclusive it is sent
    in two bytes, with the first byte having its top bit set.
  * If the number is between 16384 and (2^30 - 1) inclusive then it is sent
    in four bytes, with the first byte having its top two bits set.
  """
  if   n <= 0x7F:
    return struct.pack('>B', n)
  elif n <= 0x3FFF:
    return struct.pack('>B', (n / 256) | 0x80) + struct.pack('>B',  n % 256)
  elif n <= 0x3FFFFFFF:
    count = 1
    data = []
    while count < 4:
      data.append(struct.pack('>B', n % 256))
      n /= 256
      count += 1
    data.append(struct.pack('>B', n | 0xC0))
    data.reverse()
    return ''.join(data)
  else:
    raise BlockError("Number too large to encode")


def unpack_number(buffer, offset):
#================================
  """Decode an encoded length."""
  n = struct.unpack_from('>B', buffer, offset)[0]
  offset += 1
  if n & 0x80:
    nbr = n & 0x3F
    count = 3 if (n & 0x40) else 1
    while count > 0:
      nbr = 256*nbr + struct.unpack_from('>B', buffer, offset)[0]
      offset += 1
      count -= 1
  else:
    nbr = n
  return (nbr, offset)


class NumberUnpack(object):
#=========================

  def __init__(self):
  #-----------------
    self._count = 0
    self._nbr = 0

  def process(self, c):
  #-------------------
    n = struct.unpack('>B', c)[0]
    if self._count == 0:
      self._nbr = n
      if self._nbr & 0x80:
        self._nbr &= 0x3F
        self._count = 3 if (self._nbr & 0x40) else 1
    else:
      self._nbr = 256*self._nbr + n
      self._count -= 1
    return (self._count == 0)

  def value(self):
  #--------------
    return self._nbr


class BlockSource(threading.Thread):
#==================================
  """Start a thread to listen for incoming blocks from a file object."""

  def __init__(self, source, processblock=None, **kwds):
  #----------------------------------------------------
    """
    :param source: the file object on which data is received.
    :param processblock: a function to process received blocks. It is given
                         two parameters, the block's type and contents.

    `start()` needs to be called to actually start the receive thread. This allows
    initialisation (of other components) to be completed before having to process
    blocks. 
    """
    threading.Thread.__init__(self, **kwds)
    # Set source to be non-blocking
    flags = fcntl.fcntl(source, fcntl.F_GETFL)
    fcntl.fcntl(source, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    self._source = source
    self._processblock = processblock
    self._running = False
    self._state = 0

  def stop(self):
  #--------------
    """Stop the receive thread.

    .. note:: We need to be able to interrupt the wait on reading self._source... 
    """
    self._running = False
    self.join()


  def run(self):
  #-------------
    self._running = True
    while self._running:
      if not self._running: break
      buf = memoryview(self._source.read(READ_BLOCK_SIZE))
      ##logging.debug('READ: %s', buf.tobytes())
      i = 0
      n = len(buf)
      while i < n:
        c = buf[i]
        i += 1

        if    self._state == 0:
          if c == BLOCK_START:
            content = [ ]
            self._state = 1
        
        elif self._state == 1:
          kind = c
          self._state = 2
          decoder = NumberUnpack()

        elif self._state == 2:
          if decoder.process(c):
            blockno = decoder.value()
            self._state = 3
            decoder = NumberUnpack()

        elif self._state == 3:
          if decoder.process(c):
            length = decoder.value()
            self._state = 4

        elif self._state == 4:
          avail = min(length, n - i + 1)
          content.append(buf[i-1:i-1+avail].tobytes())
          length -= avail
          i += avail - 1
          if length == 0: self._state = 5

        elif self._state == 5:
          if c == BLOCK_END:
            body = ''.join(content)
            if self._processblock: self._processblock(kind, body)
            self._state = 0
          else:
            raise BlockError('Missing end marker')


    if self._processblock: self._processblock(-1, None)  # Indicate we have stopped


class BlockSink(object):
#======================
  """Send blocks to a file object."""


  def __init__(self, sink):
  #-----------------------
    """
    :param sink: the file object to which data is sent.
    """
    self._sink = sink
    self._lastblockno = None
    self._blocktypes = [ BLOCK_INFO, BLOCK_DATA, BLOCK_META, BLOCK_EVENT ]

  def write(self, blockno, kind, content):
  #--------------------------------------
    """
    Send a block of data.

    :param blockno: the block's number. Must be increasing.
    :param kind: the block's type.
    :param content: the block's data.
    """
    ##logging.debug("SEND '%s': %s", kind, content)
    if self._lastblockno is not None and self._lastblockno >= blockno:
      raise BlockError("Block number must be increasing")
    self._lastblockno = blockno
    if kind not in self._blocktypes:
      raise BlockError("Unknown kind of block: '%c'" % kind)
    block = []
    block.append(BLOCK_START)
    block.append(kind)
    block.append(pack_number(blockno))
    block.append(pack_number(len(content)))
    block.append(content)
    block.append(BLOCK_END)
    self._sink.write(''.join(block))
