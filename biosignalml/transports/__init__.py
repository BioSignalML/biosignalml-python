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

'''
Send and receive BioSignalML data using Web Sockets.
'''


import logging
import Queue
from time import sleep

import ws4py.client.threadedclient

from .stream import Checksum, BlockParser, SignalDataStream, StreamException

__all__ = [ 'StreamClient', 'WebStreamReader', 'WebStreamWriter', 'StreamException' ]


class StreamClient(ws4py.client.threadedclient.WebSocketClient):
#================================================================
  """
  A connection to a web socket server.

  We send a data request when the connection is established and then then parse received data.
  Received Stream Blocks found are put to `receiveQ`.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  :param request: Send to request a response.
  :type request:  :class:`~biosignalml.transports.stream.StreamBlock`
  :param receiveQ: Either a queue on which to put complete :class:`StreamBlock`\s
    or a function to call, passing a complete `StreamBlock`.
  :type receiveQ: :class:`Queue.Queue` or function
  :param check: How any checksum is treated. Default `Checksum.CHECK`
  :type check: :class:`~biosignalml.transports.stream.Checksum`
  """
  def __init__(self, endpoint, request, receiveQ, check=Checksum.CHECK, token=None, **kwds):
  #-----------------------------------------------------------------------------------------
    super(StreamClient, self).__init__(endpoint, **kwds)
    self._request = request
    self._receiver = receiveQ.put if isinstance(receiveQ, Queue.Queue) else receiveQ
    self._parser = BlockParser(self._receiver, check=check)
    self._opened = False
    self._access_key = token

  @property
  def handshake_headers(self):
  #---------------------------
    headers = super(StreamClient, self).handshake_headers
    if self._access_key is not None: headers.append(('Cookie', 'access=%s' % self._access_key))
    return headers

  def opened(self):
  #----------------
    self._opened = True                   # Now have a connection
    if self._request: self.send_block(self._request)

  def handshake_ok(self):
  #----------------------
    self._th.start()                      # Start running the thread

  def close(self, *args):
  #----------------------
    super(StreamClient, self).close(*args)

  def closed(self, code, reason=None):
  #-----------------------------------
    self._receiver(None)

  def received_message(self, msg):
  #--------------------------------
    self._parser.process(bytearray(msg.data))

  def send_block(self, block, check=Checksum.STRICT):
  #--------------------------------------------------
    '''
    Send a :class:`~biosignalml.transports.stream.StreamBlock` over a web socket.

    :param block: The block to send.
    :param check: Set to :attr:`~biosignalml.transports.stream.Checksum.STRICT`
      to append a SHA1 checksum to the block.
    '''
    while not self._opened: sleep(0.01)   # Wait until connected
    self.send(block.bytes(), True)

  def handshake_headers_getter(self):
  #----------------------------------
    return super(StreamClient, self).handshake_headers()

  def join(self, *args):
  #---------------------
    return self._th.join(*args)


class WebStreamReader(SignalDataStream):
#=======================================
  """
  An `iterator` yielding :class:`~biosignalml.transports.stream.SignalData`
  objects from a data stream server via WebSockets.

  The WebSockets client is run in a separate thread which we need to join() when finished.

  :param str endpoint: The URL of the data stream server's endpoint.
  :param uri: The URI of a :class:`~biosignalml.model.Recording` or of one or more
    :class:`~biosignalml.model.Signal`\s from which to get :class:`~biosignalml.data.TimeSeries`
    data,
  :type uri: str or list[str]
  :param start: The time, in seconds, that the first data point will be at or immediately after,
  :type start: float or None
  :param offset: The index of the first data point. An `offset` can only be given when data from a
    single signal is requested, and cannot be specified along with `start`.
  :type offset: int or None
  :param float duration: The duration, in seconds, of the :class:`~biosignalml.transports.stream.SignalData`
    returned. A value of -1 means to return the complete time series of the signal(s).

  ..todo:: Document extra parameters...
  """
  def __init__(self, endpoint, uri,
    start=None, offset=None, duration=-1, count=None, maxsize=-1, dtype=None, rate=None, units=None, **kwds):
  #---------------------------------------------------------------------------------------------------------
    super(WebStreamReader, self).__init__(endpoint, uri, start, offset, duration, count, maxsize,
                                                                                         dtype, rate, units)
    try:
      self._ws = StreamClient(endpoint, self._request, self._receiveQ, protocols=['biosignalml-ssf'], **kwds)
      self._ws.connect()
    except Exception, msg:
      logging.error('Unable to connect to WebSocket: %s', msg)
      raise StreamException('Cannot open WebStreamReader')

  def close(self):
  #---------------
    self._ws.close()

  def join(self, *args):
  #---------------------
    self._ws.join(*args)


class WebStreamWriter(object):
#=============================

  def __init__(self, endpoint, token=None):
  #----------------------------------------
    try:
      self._ws = StreamClient(endpoint, None, self.got_response, token=token,
                              protocols=['biosignalml-ssf'])
      self._ws.connect()
    except Exception, msg:
      logging.error('Unable to connect to WebSocket at %s: %s', endpoint, msg)
      raise StreamException('Cannot open WebStreamWriter')

  def close(self):
  #---------------
    self._ws.close()

  def write_block(self, block):
  #----------------------------
    self._ws.send_block(block)

  def write_signal_data(self, signaldata):
  #---------------------------------------
    self._ws.send_block(signaldata.streamblock())

  @staticmethod
  def got_response(block):
  #-----------------------
    if block and block.type == stream.BlockType.ERROR:
      logging.error("STREAM ERROR: %s:", block.content)
      raise StreamException(block.content)


if __name__ == '__main__':
#=========================

  import sys

  logging.getLogger().setLevel(logging.DEBUG)

  if len(sys.argv) < 5:
    print 'Usage: %s endpoint uri start duration' % sys.argv[0]
    sys.exit(1)

  for d in WebStreamReader(sys.argv[1], sys.argv[2], start=float(sys.argv[3]),
                                                     duration=float(sys.argv[4]) ):
    print d
