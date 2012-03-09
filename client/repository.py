######################################################
#
#  BioSignalML Project
#
#  Copyright (c) 2010-2012  David Brooks
#
#  $ID$
#
######################################################

import logging
import httplib2

import biosignalml.rdf as rdf
from biosignalml.transports import WebStreamReader, SignalData, WebStreamWriter, StreamException


class RemoteRepository(object):
#==============================
  '''
  A connection to a repository for both metadata and data.
  '''

  def __init__(self, uri, md_endpoint='/metadata/', sd_endpoint='/stream/data/'):
  #------------------------------------------------------------------------------
    self.uri = uri
    self._md_uri = uri + md_endpoint
    self._sd_uri = uri + sd_endpoint
    self._http = httplib2.Http()
    self.metadata = self.get_metadata('')

  def close(self):
  #---------------
    pass

  def get_metadata(self, uri):
  #---------------------------
    try:
      graph = rdf.Graph.create_from_resource(self._md_uri + str(uri), rdf.Format.RDFXML)
      if uri: graph.uri = rdf.Uri(uri)
      return graph
    except Exception, msg:
      raise Exception("Cannot get RDF for '%s'" % uri)

  def _send_metadata(self, uri, graph, method='POST'):
  #--------------------------------------------------
    format = rdf.Format.TURTLE ## RDFXML
    try:
      response, content = self._http.request(self._md_uri + str(uri),
        method=method,
        body=graph.serialise(base=str(uri), format=format),
        headers={'Content-type': rdf.Format.mimetype(format)})
    except Exception, msg:
      raise
    if response.status not in [200, 201]: raise Exception(content)

  def put_metadata(self, uri, graph):
  #----------------------------------
    self._send_metadata(uri, graph, 'PUT')

  def post_metadata(self, uri, graph):
  #----------------------------------
    self._send_metadata(uri, graph, 'POST')


  def get_data(self, uri, **kwds):
  #-------------------------------
    """ Gets :class:`~biosignalml.data.DataSegment'\s from the remote repository. """
    '''
    maxsize
    start
    duration
    offset
    count
    '''
    return WebStreamReader(self._sd_uri, uri, **kwds)


  def put_data(self, uri, timeseries):
  #-----------------------------------
    try:
      stream = WebStreamWriter(self._sd_uri)
      MAXPOINTS = 50000   ##### TESTING    (200K bytes if double precision)
      params = { }
      if getattr(timeseries,'rate', None):
        params['rate'] = timeseries.rate
      pos = 0
      count = len(timeseries)
      while count > 0:
        blen = min(count, MAXPOINTS)
        if getattr(timeseries, 'clock', None):
          params['clock'] = timeseries.clock[pos:pos+blen]
        stream.write_block(SignalData(uri, timeseries.time[pos], timeseries.data[pos:pos+blen], **params))
        pos += blen
        count -= blen
    except Exception, msg:
      logging.error('Error in stream: %s', msg)
      raise
    finally:
      stream.close()

