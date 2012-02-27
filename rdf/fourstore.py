######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: e4ba890 on Wed Jun 8 16:55:26 2011 +1200 by Dave Brooks $
#
######################################################

import urllib
import httplib2
import json
import logging

from triplestore import TripleStore
from formats     import Format


class FourStore(TripleStore):
#============================

  def __init__(self, href):
  #------------------------
    super(FourStore, self).__init__(href)
    self._http = httplib2.Http()

  def _request(self, endpoint, method, **kwds):
  #--------------------------------------------
    try:
      response, content = self._http.request(self._href + endpoint, method=method, **kwds)
    except AttributeError:
      raise Exception("Can not connect to 4store -- check it's running")
    #logging.debug('Request -> %s', response)
    if response.status not in [200, 201]: raise Exception(content)
    return content

  def query(self, sparql, format=Format.RDFXML):
  #---------------------------------------------
    #logging.debug('4s %s: %s', format, sparql)
    try:
      return self._request('/sparql/', 'POST',
                           body=urllib.urlencode({'query': sparql}),
                           headers={'Content-type': 'application/x-www-form-urlencoded',
                                    'Accept': Format.mimetype(format)} )
    except Exception, msg:
      logging.error('4store: %s, %s', msg, sparql)
      raise

  def ask(self, where):
  #--------------------
    return json.loads(self.query('ask where { %(where)s }' % { 'where': where }, Format.JSON))['boolean']

  def select(self, fields, where, distinct=False, limit=None):
  #-----------------------------------------------------------
    return json.loads(self.query('select%(distinct)s %(fields)s where { %(where)s }%(limit)s'
                                  % { 'distinct': ' distinct' if distinct else '',
                                      'fields': fields,
                                      'where': where,
                                      'limit': (' limit %s' % limit) if limit else '',
                                    }, Format.JSON
                                )
                     ).get('results', {}).get('bindings', [])
    """
    for result in results['results']['bindings']:
      for f in fields:
        result[f] is a dict()
           ['type']
           ['value']
           ['datatype']
           ['lang']
           ['variable']
           #types are 'uri', 'bnode', 'literal', 'typed-literal'

     [{u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#prop'},
       u's': {u'type': u'uri', u'value': u'http://www.example.org/test#bnode'},
       u'o': {u'type': u'uri', u'value': u'http://www.example.org/test#obj'} },

      {u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#prop'},
       u's': {u'type': u'bnode', u'value': u'b2'},
       u'o': {u'type': u'uri', u'value': u'http://www.example.org/test#obj'} },

      {u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#property'},
       u's': {u'type': u'uri', u'value': u'http://www.example.org/test#subject'},
       u'o': {u'type': u'uri', u'value': u'http://www.example.org/test#bnode'} },

      {u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#property'},
       u's': {u'type': u'uri', u'value': u'http://www.example.org/test#subject'},
       u'o': {u'type': u'bnode', u'value': u'b2'} },

      {u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#property'},
       u's': {u'type': u'uri', u'value': u'http://www.example.org/test#subject'},
       u'o': {u'type': u'bnode', u'value': u'b1'} },

      {u'p': {u'type': u'uri', u'value': u'http://www.example.org/test#prop'},
       u's': {u'type': u'bnode', u'value': u'b1'},
       u'o': {u'type': u'uri', u'value': u'http://www.example.org/test#obj'} }
     ]"""


  def construct(self, graph, where, params = { }, format=Format.RDFXML):
  #-----------------------------------------------------------------------
    return self.query('construct { %(graph)s } where { %(where)s }'
                        % { 'graph': graph % params,'where': where % params },
                      format)

  def describe(self, uri, format=Format.RDFXML):
  #-----------------------------------------------
    return self.query('describe <%(uri)s>' % { 'uri': uri }, format)


  def insert(self, graph, triples):
  #--------------------------------
    sparql = 'insert data { graph %(graph)s { %(triples)s } }' % { 'graph': graph,
                                                                   'triples': ' . '.join(triples) }
    #logging.debug('Insert: %s', sparql)
    content = self._request('/update/', 'POST',
                            body=urllib.urlencode({'update': sparql}),
                            headers={'Content-type': 'application/x-www-form-urlencoded'})
    if 'error' in content: raise Exception(content)


  def extend_graph(self, graph, rdfdata, format=Format.RDFXML):
  #--------------------------------------------------------------
    #logging.debug('Extend <%s>: %s', graph, rdfdata)
    self._request('/data/', 'POST',
                  body=urllib.urlencode({'data': rdfdata,
                                         'graph': str(graph),
                                         'mime-type': Format.mimetype(format),
                                        }),
                  headers={'Content-type': 'application/x-www-form-urlencoded'})

  def replace_graph(self, graph, rdf, format=Format.RDFXML):
  #-----------------------------------------------------------
    #logging.debug('Replace <%s>: %s', graph, rdf)
    self._request('/data/' + str(graph), 'PUT', body=rdf, headers={'Content-type': Format.mimetype(format)})

  def delete_graph(self, graph):
  #-----------------------------
    #logging.debug('Delete <%s>', graph)
    self._request('/data/' + str(graph), 'DELETE')


  def fulltext(self):
  #------------------
    self.extend_graph('system:config',
     """@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix dc:   <http://purl.org/dc/elements/1.1/> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix text: <http://4store.org/fulltext#> .

        rdfs:label      text:index text:stem .
        rdfs:comment    text:index text:stem .
        dc:description  text:index text:stem .
        dcterms:description text:index text:stem .""")


if __name__ == '__main__':
#=========================

  import os, sys
  import argparse

  parser = argparse.ArgumentParser(description="Test and setup a 4store triplestore")
  parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                    help="Enable debug trace")
  parser.add_argument("--fulltext", dest="fulltext", action="store_true",
                    help="Configure the store for full text indexing")
  parser.add_argument("--test", dest="test", action="store_true",
                    help="Run some simple tests")
  parser.add_argument("store", metavar="URI", help="URI of the triplestore")
  args = parser.parse_args()

  if args.debug: logging.getLogger().setLevel(logging.DEBUG)

  store = FourStore(args.store)

  if args.test:

    print 'ASK:\n',      store.ask('?s ?p ?o')
    print '\nQUERY:\n',  store.query('select ?s ?p ?o where { ?s ?p ?o } limit 10')
    print 'SELECT:\n', store.select('?s ?p ?o', '?s ?p ?o', limit=10)

    store.insert('<http://example.com/G>',
                   [ '<http://example.com/s> <http://example.com/p> "o"' ])
    print '\nGRAPH SELECT:\n',    store.select('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')
    print '\nGRAPH CONSTRUCT:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.extend_graph('http://example.com/G', '<http://example.com/S> <http://example.com/P> "b" .')
    print 'EXTENDED:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.replace_graph('http://example.com/G', '<http://example.com/S> <http://purl.org/dc/terms/description> "There are lots of mice!" .')
    print 'REPLACED:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.delete_graph('http://example.com/G')
    print 'DELETED:\n',  store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')

  elif args.fulltext:

    store.fulltext()
