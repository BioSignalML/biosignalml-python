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

import logging
import httplib2

import biosignalml.rdf as rdf
from biosignalml.transports import BlockType, SignalData
from biosignalml.transports import WebStreamReader, WebStreamWriter, StreamException


class RemoteRepository(object):
#==============================
  '''
  A connection to a repository for both metadata and data.
  '''

  def __init__(self, uri, access_key=None, md_endpoint=None, sd_endpoint=None):
  #----------------------------------------------------------------------------
    self.uri = uri
    self._access_key = access_key
    self._md_uri = uri + md_endpoint if md_endpoint is not None else ''
    self._sd_uri = uri + sd_endpoint if sd_endpoint is not None else ''
    self._http = httplib2.Http()
    self.metadata = self.get_metadata(uri)

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
    headers={'Content-type': rdf.Format.mimetype(format)}
    if self._access_key is not None: headers['Cookie'] = 'access=%s' % self._access_key
    try:
      response, content = self._http.request(self._md_uri + str(uri),
        body=graph.serialise(base=str(uri), format=format),
        method=method, headers=headers)
    except Exception, msg:
      raise
    if   response.status == 401: raise Exception("Unauthorised")
    elif response.status not in [200, 201]: raise Exception(content)
    return response.get('location')

  def put_metadata(self, uri, graph):
  #----------------------------------
    return self._send_metadata(uri, graph, 'PUT')

  def post_metadata(self, uri, graph):
  #----------------------------------
    return self._send_metadata(uri, graph, 'POST')


  def get_data(self, uri, **kwds):
  #-------------------------------
    """ Gets :class:`~biosignalml.data.DataSegment`\s from the remote repository. """
    '''
    maxsize
    start
    duration
    offset
    count
    dtype
    '''
    for block in WebStreamReader(self._sd_uri+uri, uri, **kwds):
      if block.type == BlockType.DATA: yield block.signaldata()


  def put_data(self, uri, timeseries):
  #-----------------------------------
    stream = None
    try:
      stream = WebStreamWriter(self._sd_uri+uri)
      MAXPOINTS = 50000   ##### TESTING    (200K bytes if double precision)
      params = { }
      if hasattr(timeseries, 'rate'): params['rate'] = timeseries.rate
      pos = 0
      count = len(timeseries)
      while count > 0:
        blen = min(count, MAXPOINTS)
        if hasattr(timeseries, 'clock'):
          params['clock'] = timeseries.clock[pos:pos+blen]
        stream.write_signal_data(SignalData(uri, timeseries.time[pos], timeseries.data[pos:pos+blen], **params))
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
