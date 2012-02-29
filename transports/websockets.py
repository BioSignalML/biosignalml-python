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


import logging

import ws4py.client.threadedclient

import stream


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
  :param receiveQ: A queue on which to put complete `StreamBlock`'s. `None` is
   sent when the stream has finished.
  :type receiveQ: :class:`Queue.Queue`
  :param check: How any checksum is treated. Default `Checksum.CHECK`
  :type check: :class:`~biosignalml.transports.stream.Checksum`
  """
  def __init__(self, endpoint, request, receiveQ, check=stream.Checksum.CHECK, **kwds):
  #------------------------------------------------------------------------------------
    ws4py.client.threadedclient.WebSocketClient.__init__(self, endpoint, **kwds)
    self._request = request
    self._receiveQ = receiveQ
    self._parser = stream.BlockParser(receiveQ, check=check)

  def opened(self):
  #----------------
    self.send_block(self._request)

  def closed(self, code, reason=None):
  #-----------------------------------
    self._receiveQ.put(None)
      
  def received_message(self, msg):
  #--------------------------------
    self._parser.process(msg.data)

  def send_block(self, block, check=stream.Checksum.STRICT):
  #---------------------------------------------------------
    '''
    Send a :class:`~biosignalml.transports.stream.StreamBlock` over a web socket.

    :param block: The block to send.
    :param check: Set to :attr:`~biosignalml.transports.stream.Checksum.STRICT`
      to append a MD5 checksum to the block.
    '''
    logging.debug('SEND: %s', block)
    self.send(block.bytes(), True)


class WebStreamReader(stream.SignalDataStream):
#==============================================
  """
  An `iterator` yielding :class:`~biosignalml.transports.stream.SignalData`
  objects from a data stream server via Web Sockets.

  :param endpoint: The URL of the data stream server's endpoint.
  :type endpoint: str
  :param uri: The URI of a :class:`~biosignalml.model.Recording` or of one or more
    :class:`~biosignalml.model.Signal`\s from which to get :class:`~biosignalml.model.data.TimeSeries`
    data,
  :type uri: str or list[str]
  :param start: The time, in seconds, that the first data point will be at or immediately after,
  :type start: float or None
  :param offset: The index of the first data point. An `offset` can only be given when data from a
    single signal is requested, and cannot be specified along with `start`.
  :type offset: integer or None
  :param duration: The duration, in seconds, of the :class:`~biosignalml.transports.stream.TimeSeries`
    returned. A value of -1 means to return the complete time series of the signal(s).
  :type duration: float
  """
  def __init__(self, endpoint, uri, start=None, offset=None, duration=-1, count=None, maxsize=-1):
  #------------------------------------------------------------------------------------------------
    stream.SignalDataStream.__init__(self, endpoint, uri, start, offset, duration, count, maxsize)
    try:
      self._ws = StreamClient(endpoint, self._request, self._receiveQ, protocols=['biosignalml-ssf'])
      self._ws.connect()
    except Exception, msg:
      logging.error('Unable to connect to WebSocket: %s', msg)
      raise stream.StreamException('Cannot open WebStreamReader')

  def close(self):
  #---------------
    self._ws.close()


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
