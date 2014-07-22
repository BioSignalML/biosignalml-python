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

import os
import tempfile
import socket
import logging

import urllib
import httplib2
httplib2.RETRIES = 1

import biosignalml.rdf as rdf
from biosignalml.rdf.sparqlstore import SparqlUpdateStore
from biosignalml.repository import BSMLUpdateStore

__all__ = [ 'RemoteSparqlStore', 'RemoteRepository' ]


class RemoteSparqlStore(SparqlUpdateStore):
#==========================================
  """
  Connect to SPARQL endpoints on a BioSignalML repository.

  """
  ENDPOINTS = [ '/sparql/update/', '/sparql/graph/' ] #: Order is UPDATE, GRAPH

  def __init__(self, uri, token, port=None):
  #-----------------------------------------
    super(RemoteSparqlStore, self).__init__(uri, port=port)
    self._token = token

  def http_request(self, endpoint, method, body=None, headers=None):
  #-----------------------------------------------------------------
    if self._token is not None: headers['Cookie'] = 'access=%s' % self._token
    return self._request(endpoint, method, body, headers)


class RemoteRepository(BSMLUpdateStore):
#=======================================
  """
  A connection to a repository for both metadata and data.

  :param uri: The web address of the repository.
  :param name: An optional user name for authenticating access to the repository.
  :param password: A password to use with the `name`.


  .. note:: Authentication

     If no `name` is supplied the file `~/.bsml/tokens` is read to find the
     last valid access token used for the repository; if both a `name` and `password`
     is supplied then they are sent to the repository's authentication service and,
     if valid, an access token is saved in `~/.bsml/tokens`.

     The `access_token` property will be None if a valid access token cannot be
     obtained. The repository though may still be usable, as it guest access may
     be allowed.

  """

  def __init__(self, uri, name=None, password=None, md_endpoint=None, sd_endpoint=None, port=None):
  #------------------------------------------------------------------------------------------------
    self.uri = uri
    if name in [None, '']: self._get_access()   # Sets self._token
    else:                  self._authenticate(name, password)
    super(RemoteRepository, self).__init__(uri, RemoteSparqlStore(uri, self._token, port=port))
    self._md_uri = uri + md_endpoint if md_endpoint is not None else ''
    self._sd_uri = uri + sd_endpoint if sd_endpoint is not None else ''
    self.metadata = self.get_metadata(uri)

  def close(self):
  #---------------
    pass

  @staticmethod
  def _get_token_file():
  #---------------------
    path = os.getenv('HOME') + '/.bsml'
    try: os.makedirs(path)
    except OSError: pass
    try:
      return open(path + '/' + 'tokens', 'r+')
    except IOError:
      return open(path + '/' + 'tokens', 'w+')

  @staticmethod
  def _find_token(uri):
  #--------------------
    r = (None, None)
    f = RemoteRepository._get_token_file()
    for l in f:
      p = l.split()
      if uri == p[0] and len(p) > 1:
        r = (p[1], p[3])   # (token, expiry)
        break
    f.close()
    return r

  def _get_access(self):
  #---------------------
    self._token, self._expiry = self._find_token(str(self.uri))

  def _save_access(self, access):    # "token name expiry"
  #------------------------------
    f = self._get_token_file()
    g = tempfile.NamedTemporaryFile(delete=True)
    existing = False
    uri = str(self.uri)
    for l in f:
      if uri == l.split()[0]:
        existing = True
        g.write('%s %s\n' % (uri, access))
      else:
        g.write(l)
    if not existing:
      g.write('%s %s\n' % (uri, access))
    g.flush()
    f.seek(0)
    f.truncate()
    g.seek(0)
    for l in g: f.write(l)
    f.close()
    g.close()

  def _authenticate(self, name, password):
  #---------------------------------------
    self._token = self._expiry = None
    body = {'action': 'Token', 'username': name}
    if password is not None: body['password'] = password
    remote = httplib2.Http()
    try:
      response, access = remote.request(str(self.uri) + '/frontend/login',
        method='POST', body=urllib.urlencode(body),
        headers={'Content-type': 'application/x-www-form-urlencoded'})
    except Exception, msg:
      raise IOError(msg)
    if response.status == 200:
      self._save_access(access)
      p = access.split()
      self._token = p[0]
      self._expiry = p[2]
    else:
      self._save_access('')

  @property
  def access_token(self):
  #----------------------
    return self._token

  @property
  def access_expiry(self):
  #----------------------
    return self._expiry

  @staticmethod
  def known_repositories():
  #------------------------
    f = RemoteRepository._get_token_file()
    r = [ l.split()[0] for l in f ]
    f.close()
    return r

  @staticmethod
  def authenticated(uri):
  #----------------------
    token = RemoteRepository._find_token(uri)[0]
    if token is None: return False
    body = {'action': 'Validate', 'token': token}
    remote = httplib2.Http()
    try:
      response, access = remote.request(uri + '/frontend/login',
        method='POST', body=urllib.urlencode(body),
        headers={'Content-type': 'application/x-www-form-urlencoded'})
    except Exception, msg:
      raise IOError(msg)
    return (response.status == 200)


  def get_metadata(self, uri):
  #---------------------------
    try:
      graph = rdf.Graph.create_from_resource(self._md_uri + str(uri), rdf.Format.RDFXML)
      if uri: graph.uri = rdf.Uri(uri)
      return graph
    except Exception, msg:
      raise IOError("Cannot get RDF for '%s' (%s)" % (uri, msg))

  def _send_metadata(self, method, uri, metadata, format):
  #-------------------------------------------------------
    headers={'Content-type': rdf.Format.mimetype(format)}
    if self._token is not None: headers['Cookie'] = 'access=%s' % self._token
    endpoint = self._md_uri + str(uri)
    try:
      http = httplib2.Http(timeout=20)
      response, content = http.request(endpoint, body=metadata, method=method, headers=headers)
    except socket.error, msg:
      raise IOError("Cannot connect to repository: %s" % endpoint)
    if   response.status == 401: raise IOError("Unauthorised")
    elif response.status not in [200, 201]: raise IOError("%s: %s" % (response.status, content))
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
