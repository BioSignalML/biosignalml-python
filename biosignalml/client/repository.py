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

import socket
import logging

import httplib2
httplib2.RETRIES = 1

import biosignalml.rdf as rdf
from biosignalml.rdf.sparqlstore import SparqlUpdateStore
from biosignalml.repository import BSMLUpdateStore


class RemoteSparqlStore(SparqlUpdateStore):
#==========================================
  """
  Connect to SPARQL endpoints on a BioSignalML repository.

  """
  ENDPOINTS = [ '/sparql/update/', '/sparql/graph/' ] #: Order is UPDATE, GRAPH

  def __init__(self, uri, access_key, port=None):
  #----------------------------------------------
    super(RemoteSparqlStore, self).__init__(uri, port=port)
    self._access_key = access_key

  def http_request(self, endpoint, method, body=None, headers=None):
  #-----------------------------------------------------------------
    if self._access_key is not None: headers['Cookie'] = 'access=%s' % self._access_key
    return self._request(endpoint, method, body, headers)


class RemoteRepository(BSMLUpdateStore):
#=======================================
  '''
  A connection to a repository for both metadata and data.
  '''

  def __init__(self, uri, access_key=None, md_endpoint=None, sd_endpoint=None, port=None):
  #---------------------------------------------------------------------------------------
    self.uri = uri
    self._access_key = access_key
    super(RemoteRepository, self).__init__(uri, RemoteSparqlStore(uri, access_key, port=port))
    self._md_uri = uri + md_endpoint if md_endpoint is not None else ''
    self._sd_uri = uri + sd_endpoint if sd_endpoint is not None else ''
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
      raise IOError("Cannot get RDF for '%s'" % uri)

  def _send_metadata(self, method, uri, metadata, format):
  #-------------------------------------------------------
    headers={'Content-type': rdf.Format.mimetype(format)}
    if self._access_key is not None: headers['Cookie'] = 'access=%s' % self._access_key
    endpoint = self._md_uri + str(uri)
    try:
      http = httplib2.Http(timeout=20)
      response, content = http.request(endpoint, body=metadata, method=method, headers=headers)
    except socket.error, msg:
      raise IOError("Cannot connect to repository: %s" % endpoint)
    if   response.status == 401: raise IOError("Unauthorised")
    elif response.status not in [200, 201]: raise IOError(content)
    return response.get('location')

  def put_metadata(self, uri, metadata, format=rdf.Format.RDFXML):
  #---------------------------------------------------------------
    return self._send_metadata('PUT', uri, metadata, format)

  def post_metadata(self, uri, metadata, format=rdf.Format.RDFXML):
  #----------------------------------------------------------------
    return self._send_metadata('POST', uri, metadata, format)


if __name__ == "__main__":
#=========================

  repo = RemoteRepository('http://devel.biosignalml.org')

  rec_uri = 'http://devel.biosignalml.org/fph/icon/120312170352/FLW0002'

  sig_uri = rec_uri + '/signal/0'

  for d in repo.get_data(rec_uri):
    print d

  for d in repo.get_data(sig_uri):
    print d
