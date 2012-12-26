######################################################
#
#  BioSignalML Project
#
#  Copyright (c) 2010-2012  David Brooks
#
#  $ID: c1bb582 on Tue May 1 10:48:29 2012 +1200 by Dave Brooks $
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

  @classmethod
  def connect(cls, uri, **kwds):
  #-----------------------------
    self = cls(uri, **kwds)
    return self

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
    format = rdf.Format.RDFXML
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
    """ Gets :class:`~biosignalml.data.DataSegment`\s from the remote repository. """
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
    stream = None
    try:
      stream = WebStreamWriter(self._sd_uri)
      MAXPOINTS = 50000   ##### TESTING    (200K bytes if double precision)
      params = { }
      if hasattr(timeseries, 'rate'): params['rate'] = timeseries.rate
      pos = 0
      count = len(timeseries)
      while count > 0:
        blen = min(count, MAXPOINTS)
        if hasattr(timeseries, 'clock'):
          params['clock'] = timeseries.clock[pos:pos+blen]
        stream.write_block(SignalData(uri, timeseries.time[pos], timeseries.data[pos:pos+blen], **params))
        pos += blen
        count -= blen
    except Exception, msg:
      logging.error('Error in stream: %s', msg)
      raise
    finally:
      if stream: stream.close()


if __name__ == "__main__":
#=========================

  repo = RemoteRepository('http://devel.biosignalml.org')

  rec_uri = 'http://devel.biosignalml.org/fph/icon/120312170352/FLW0002'

  sig_uri = rec_uri + '/signal/0'

  for d in repo.get_data(rec_uri):
    print d

  for d in repo.get_data(sig_uri):
    print d
