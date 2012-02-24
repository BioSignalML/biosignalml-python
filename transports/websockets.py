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
  def __init__(self, endpoint, request, receiveQ, check=stream.Checksum.CHECK, **kwds):
  #------------------------------------------------------------------------------------
    ws4py.client.threadedclient.WebSocketClient.__init__(self, endpoint, **kwds)
    self._request = request
    self._receiveQ = receiveQ
    self._parser = stream.BlockParser(receiveQ, check=check)

  def opened(self):
  #----------------
    self.send(self._request)

  def closed(self, code, reason=None):
  #-----------------------------------
    self._receiveQ.put(None)
      
  def received_message(self, msg):
  #--------------------------------
    self._parser.process(msg.data)



class WebStreamReader(stream.SimpleStreamReader):
#================================================
  """
  An `iterator` yielding :class:`StreamData` objects from a data stream server via Web Sockets.

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
    stream.SimpleStreamReader.__init__(self, endpoint, uri, start, duration)
    try:
      self._ws = WebSocketReadStream(endpoint, self._request, self._receiveQ, protocols=['biosignalml-ssf'])
      self._ws.connect()
    except Exception, msg:
      logging.error('Unable to connect to WebSocket: %s', msg)
      raise IOError('Cannot open StreamDataReader')

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

  for d in WebStreamReader(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) ):
    print d
