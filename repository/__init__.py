######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: __init__.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import os
import logging

import RDF as librdf
import json

from tornado.options import options

import biosignalml.formats

from biosignalml import BSML, Recording, Signal, Event, Annotation
from biosignalml.utils import xmlescape

from biosignalml.rdf import RDF, DCTERMS, PRV
from biosignalml.rdf import Uri, Node, Resource, BlankNode, Graph, Statement
from biosignalml.rdf import Format

from provenance import Provenance


class Repository(object):
#========================
  '''
  An RDF repository storing triples in named graphs and tracking graph provenance.

  :param base_uri:
  :param store_uri:
  '''
  def __init__(self, base_uri, triplestore):
  #-----------------------------------------
    self.uri = base_uri
    self._triplestore = triplestore
    self._provenance = Provenance(self.uri + '/provenance')

  def __del__(self):
  #-----------------
    logging.debug('Repository shutdown')
    del self._provenance
    del self._triplestore

  def provenance_uri(self):
  #------------------------
    return self._provenance.uri

  def graph_has_provenance(self, graph):
  #-------------------------------------
    ''' Check a URI is that of a recording graph for which we have provenance.'''
    return self._triplestore.ask(
      '''graph <%(pgraph)s> { <%(obj)s> a bsml:RecordingGraph }
         graph <%(obj)s> { ?s ?p ?o }''',
      params=dict(pgraph=self._provenance.uri, obj=graph),
      prefixes=dict(bsml=BSML.prefix))


  def get_current_resources(self, rtype):
  #--------------------------------------
    """
    Return a list of URI's in a given class that are in recording graphs which have provenance.

    :param rtype: The class of resource to find.
    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    """
    return [ Uri(r['r']['value']) for r in self._triplestore.select(
      '?r',
      '''graph <%(pgraph)s> { ?g a bsml:RecordingGraph MINUS { [] prv:precededBy ?g }}
         graph ?g { ?r a <%(rtype)s> }''',
      params=dict(pgraph=self._provenance.uri, rtype=rtype),
      prefixes=dict(bsml=BSML.prefix, prv=PRV.prefix),
      distinct=True,
      order='?r')
      ]

  def get_current_resource_and_graph(self, uri, rtype):
  #----------------------------------------------------
    """
    Return the resource and graph URIS where the graph has provenance, contains a specific object,
     and the resource is of the given type.

    :param uri: The URI of an object.
    :param rtype: The class of resource the graph has to have.
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    for r in self._triplestore.select(
      '?r ?g',
      '''graph <%(pgraph)s> { ?g a bsml:RecordingGraph MINUS { [] prv:precededBy ?g }}
         graph ?g { ?r a <%(rtype)s> . <%(obj)s> a [] }''',
      params=dict(pgraph=self._provenance.uri, rtype=rtype, obj=uri),
      prefixes=dict(bsml=BSML.prefix, prv=PRV.prefix)
      ): return (Uri(r['r']['value']), Uri(r['g']['value']))
    return (None, None)

  def has_current_resource(self, uri, rtype):
  #------------------------------------------
    return self._triplestore.ask(
      '''graph <%(pgraph)s> { ?g a bsml:RecordingGraph MINUS { [] prv:precededBy ?g }}
         graph ?g { <%(obj)s> a <%(rtype)s> }''',
      params=dict(pgraph=self._provenance.uri, rtype=rtype, obj=uri))


  def update(self, uri, triples):
  #------------------------------
    self._triplestore.update(uri, triples)


  def replace_graph(self, uri, rdf, format=Format.RDFXML):
  #-------------------------------------------------------
    #### graph.append(Statement(graph.uri, DCTERMS._provenance, self._provenance.add(graph.uri)))

    # If graph already present then rename (to new uuid()) and add
    # provenance...

    # add version statement to graph ??
    # What about actual recording file(s)? They should also be renamed...

    self._triplestore.replace_graph(uri, rdf, format=format)

    #  Generate provenance....


    #for k, v in provenance.iter_items():
    #  self._provenance.add(self.uri, content-type, hexdigest, ...)
    #self._triplestore.insert(self._provenace, triples...)


  def extend_graph(self, uri, rdf, format=Format.RDFXML):
  #---------------------------------------------------
    self._triplestore.extend_graph(uri, rdf, format=format)


  def delete_graph(self, uri):
  #---------------------------
    self._triplestore.delete_graph(uri)
    #self._provenance.delete_graph(uri)
    ## Should this set provenance...


  def query(self, sparql, header=False, html=False, abbreviate=False):
  #-------------------------------------------------------------------
    return QueryResults(self, sparql, header, html, abbreviate)


  def construct(self, template, where, params=None, graph=None, format=Format.RDFXML, prefixes=None):
  #--------------------------------------------------------------------------------------------------
    return self._triplestore.construct(template, where, params, graph, format, prefixes)


  def describe(self, uri, format=Format.RDFXML):
  #---------------------------------------------
    return self._triplestore.describe(uri, format)

  def ask(self, query, graph=None):
  #--------------------------------
    return self._triplestore.ask(query, graph)

  def get_subjects(self, prop, obj, graph=None, ordered=False):
  #------------------------------------------------------------
    if isinstance(obj, Resource) or isinstance(obj, Uri):
      obj = '<%s>' % obj
    elif not isinstance(obj, Node):
      obj = '"%s"' % obj
    return [ r['s']['value'] for r in
                  self._triplestore.select('?s', '?s <%(prop)s> %(obj)s',
                                            params = dict(prop=prop, obj=obj),
                                            graph = graph,
                                            order = '?s' if ordered else None) ]

  def get_objects(self, subj, prop, graph=None):
  #---------------------------------------------
    """
    Get objects of all statements that match a given subject/predicate.
    """
    objects = []
    for r in self._triplestore.select('?o', '<%(subj)s> <%(prop)s> ?o',
                                      params = dict(subj = subj, prop=prop),
                                      graph = graph):
      if   r['o']['type'] == 'uri':           objects.append(Resource(Uri(r['o']['value'])))
      elif r['o']['type'] == 'bnode':         objects.append(BlankNode(r['o']['value']))
      elif r['o']['type'] == 'literal':       objects.append(r['o']['value'])
      elif r['o']['type'] == 'typed-literal': objects.append(r['o']['value']) ## check datatype and convert...
    return objects

  def make_graph(self, uri, template, where=None, params=None, graph=None, prefixes=None):
  #---------------------------------------------------------------------------------------
    '''
    Construct a RDF graph from a query against the repository/

    :param uri: URI of the resulting graph.
    :rtype: :class:`~biosignalml.rdf.Graph`
    '''
    if where is None: where = template
    rdf = self.construct(template, where, params=params, graph=graph, format=Format.RDFXML, prefixes=prefixes)
    ##logging.debug("Statements: %s", rdf)  ###
    return Graph.create_from_string(uri, rdf, Format.RDFXML)

  def get_types(self, uri, graph):
  #------------------------------
    return self.get_objects(uri, RDF.type, graph)


  def describe(self, uri, graph=None, format=Format.RDFXML):
  #---------------------------------------------------------

    def description(uri, graph, format):
    #-----------------------------------
      return self.construct('?s ?p ?o', '?s ?p ?o FILTER (?p != <http://4store.org/fulltext#stem>'
                                                     + (' && (?s = <%(uri)s> || ?o = <%(uri)s>))'
                                                              % dict(uri=uri)) if uri else '',
                             graph=graph, format=format)
    class Closure(Graph):
    #--------------------
      def __init__(self, rdf, base, format):
        Graph.__init__(self)
        self._base = base
        self._urns = set()
        for stmt in Graph.create_from_string(base, rdf, format):
          self.append(stmt)
          self.add_urn(stmt.subject)
          self.add_urn(stmt.object)

      def add_urn(self, node):
        if Resource.is_uuid_urn(node) and str(node) not in self._urns:
          ttl = description(node, None, Format.TURTLE)
          self._urns.add(str(node))
          for stmt in Graph.create_from_string(self._base, ttl, Format.TURTLE):
            self.append(stmt)
            ##print '[%s, %s, %s]' % (stmt.subject, stmt.predicate, stmt.object)
            if node != stmt.subject: self.add_urn(stmt.subject)
            if node != stmt.object: self.add_urn(stmt.object)

    ttl = description(uri, graph, format)
    return Closure(ttl, self.uri, format).serialise(format, base = self.uri + '/')  # Need '/' for Tabulator...


class BSMLRepository(Repository):
#================================
  '''
  An RDF repository containing BioSignalML metadata.
  '''

  def has_recording(self, uri):
  #----------------------------
    ''' Check a URI refers to a Recording. '''
    return self.has_current_resource(uri, BSML.Recording)

  def has_signal(self, uri):
  #-------------------------
    ''' Check a URI refers to a Signal. '''
    return self.has_current_resource(uri, BSML.Signal)

  def has_signal_in_recording(self, sig, rec):
  #-------------------------------------------
    ''' Check a URI refers to a Signal in a given Recording. '''
    return (self.has_current_resource(rec, BSML.Recording)
        and self.has_current_resource(uri, BSML.Signal))

  def recordings(self):
  #--------------------
    """
    Return a list of URI's of the Recordings in the repository.

    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    """
    return self.get_current_resources(BSML.Recording)

  def get_recording_and_graph_uri(self, uri):
  #------------------------------------------
    """
    Get the URIs of the recording and its Graph that contain the object.

    :param uri: The URI of some object.
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    return self.get_current_resource_and_graph(uri, BSML.Recording)

  def get_recording(self, uri):
  #----------------------------
    '''
    Get the Recording from the graph that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    '''
    #logging.debug('Getting: %s', uri)
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    #logging.debug('Graph: %s', graph_uri)
    if graph_uri is not None:
      rclass = biosignalml.formats.CLASSES.get(
                 str(self.get_objects(rec_uri, DCTERMS.format, graph=graph_uri))[0],
                 Recording)
      graph = self.make_graph(graph_uri, '?s ?p ?o', graph=graph_uri)
      return rclass.create_from_graph(rec_uri, graph, signals=False)
    else:
      return None

  def get_recording_with_signals(self, uri):
  #-----------------------------------------
    """
    Get the Recording with its Signals from the graph
      that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    """
    rec = self.get_recording(uri)
    if rec is not None:
      for r in rec.graph.query("select ?s where { ?s a <%s> . ?s <%s> <%s> } order by ?s"
                               % (BSML.Signal, BSML.recording, rec.uri)):
        rec.add_signal(rec.SignalClass.create_from_graph(str(r['s']), rec.graph, units=None))
    return rec

  def store_recording(self, recording):
  #------------------------------------
    """
    Store a recording's metadata in the repository.

    :param recording: The :class:`~biosignalml.Recording` to store.
    """
    self.replace_graph(recording.uri, recording.metadata_as_graph().serialise())


#  def signal_recording(self, uri):
#  #-------------------------------
#    return self.get_object(uri, BSML.recording)

  def get_signal(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get a Signal from the repository.

    :param uri: The URI of a Signal.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Signal`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a  bsml:Signal . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.NS.prefix),
                            graph = graph_uri
                            )
    return Signal.create_from_graph(uri, graph, units=None)  # units set from graph...

#  def signal(self, sig, properties):              # In context of signal's recording...
#  #---------------------------------
#    if self.check_type(sig, BSML.Signal):
#      r = [ [ Graph.make_literal(t, '') for t in self.get_objects(sig, p) ] for p in properties ]
#      r.sort()
#      return r
#    else: return None


  def get_event(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get an Event from the repository.

    :param uri: The URI of an Eventt.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Event`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a  bsml:Event . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.prefix),
                            graph = graph_uri
                            )
    return Event.create_from_graph(uri, graph, eventtype=None)  # eventtype set from graph...

  def get_annotation(self, uri, graph_uri=None):
  #---------------------------------------------
    '''
    Get an Annotation from the repository.

    :param uri: The URI of an Annotation.
    :rtype: :class:`~biosignalml.Annotation`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    if graph_uri is None: return None
    graph = self.make_graph(uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a bsml:Annotation . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.prefix),
                            graph = graph_uri
                            )
    return Annotation.create_from_graph(uri, graph)

#  def get_annotation_by_content(self, uri, graph_uri=None):
#  #--------------------------------------------------------
#    '''
#    Get an Annotation from the repository identified by its body content.
#
#    :param uri: The URI of the body of an Annotation.
#    :rtype: :class:`~biosignalml.Annotation`
#    '''
#    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
#    for r in self._triplestore.select('?a', 'graph <%(g)s> { ?a a oa:Annotation . ?a oa:hasBody <%(u)s> }',
#                                      params = dict(g=graph_uri, u=uri),
#                                      prefixes = dict(oa = OA.prefix),
#                                      ):
#      return self.get_annotation(r['a']['value'], graph_uri)

  def annotations(self, uri, graph_uri=None):
  #------------------------------------------
    '''
    Return a list of all Annotations about a subject.

    :param uri: The URI of the subject.
    :rtype: list of URIs to oa:Annotations
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    return [ (r['a']['value'])
      for r in self._triplestore.select('?a',
        '?a a bsml:Annotation . ?a bsml:about <%s> . optional { ?a dct:created ?tm }' % uri,
        graph = graph_uri,
        prefixes = dict(bsml=BSML.prefix, dct=DCTERMS.prefix),
        order = '?a ?tm') ]


class SparqlHead(object):
#========================
  import pyparsing as parser

  uri = parser.QuotedString('<', endQuoteChar='>')
  head = parser.ZeroOrMore(
      parser.Group(parser.Keyword('base', caseless=True) + uri)
    | parser.Group(parser.Keyword('prefix', caseless=True)
       + parser.Group(parser.Combine(
           parser.Optional(parser.Word(parser.alphas, parser.alphanums)) + parser.Suppress(':')
           ) + uri))
         )
  @staticmethod
  def parse(sparql):
  #-----------------
    return SparqlHead.head.parseString(sparql)

"""([(['prefix', (['owl', 'http://www.w3.org/2002/07/owl#'], {})], {}),
     (['prefix', (['rdfs', 'http://www.w3.org/2000/01/rdf-schema#'], {})], {}),
     (['prefix', (['tl', 'http://purl.org/NET/c4dm/timeline.owl#'], {})], {}),
     (['prefix', (['rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'], {})], {}),
     (['prefix', (['xsd', 'http://www.w3.org/2001/XMLSchema#'], {})], {}),
     (['prefix', (['dc', 'http://purl.org/dc/terms/'], {})], {}),
     (['prefix', (['evt', 'http://purl.org/NET/c4dm/event.owl#'], {})], {}),
     (['base', 'http://repository.biosignalml.org/recording/'], {}),
     (['prefix', (['bsml', '%s' % BSML.uri], {})], {}),
     (['prefix', (['text', 'http://4store.org/fulltext#'], {})], {})
    ], {})"""



class QueryResults(object):
#==========================

  def __init__(self, repo, sparql, header=False, html=False, abbreviate=False):
  #----------------------------------------------------------------------------
    self._repobase = repo.uri
    self._set_prefixes(sparql)
    self._header = header
    self._html = html
    self._abbreviate = abbreviate
    #logging.debug('SPARQL: %s', sparql)
    try:
      self._results = json.loads(repo._triplestore.query(sparql, Format.JSON))
    except Exception, msg:
      self._results = { 'error': str(msg) }

  def _set_prefixes(self, sparql):
  #-------------------------------
    self._base = None
    self._prefixes = { }
    header = SparqlHead.parse(sparql)
    for h in header:
      if h[0] == 'base':
        self._base = h[1]
      else:       # 'prefix'
        self._prefixes[h[1][0]] = h[1][1]
    #logging.debug('PFX: %s', self._prefixes)

  def abbreviate_uri(self, uri):
  #-----------------------------
    for name, prefix in self._prefixes.iteritems():
      if uri.startswith(prefix): return '%s:%s' % (name, uri[len(prefix):])
    if self._base and uri.startswith(self._base): return '<%s>' % uri[len(self._base):]
    return '<%s>' % uri

  def _add_html(self, result):
  #---------------------------
    rtype = result.get('type')
    value = result.get('value')
    if   rtype == 'uri':
      uri = self.abbreviate_uri(value) if self._abbreviate else uri
      if uri[0] == '<':
        uri = uri[1:-1]
        LT = '&lt;'
        GT = '&gt;'
      else:
        LT = GT = ''
      if value.startswith(self._repobase):
        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
                       % (LT,
                          '/repository/' + value[len(options.resource_prefix):],
                          value, uri,
                          GT))
                 ## '/repository/' is web-server path to view objects in repository
      ## Following needs work...
#      elif value.startswith('http://physionet.org/'): ########### ... URI to a Signal, Recording, etc...
#        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
#                       % (LT,
#                          '/repository/' + value.replace(':', '%3A', 1),
#                          value, uri,
#                          GT))
#                 ## '/repository/' is web-server path to view objects in repository
      else:
        result['html'] = '%s%s%s' % (LT, uri, GT)
    elif rtype == 'bnode':
      result['html'] = '_:' + value
    #elif rtype == 'literal':
    #  return value              ## set @lang, ^^datatype (or convert to data type) ??
    #elif rtype == 'typed-literal':
    #  return value
    else:
      result['html'] = xmlescape(value)

    return result

  def __iter__(self):
  #------------------
    #logging.debug('DATA: %s', self._results)
    # self._results are as per http://www.w3.org/TR/rdf-sparql-json-res/
    #                      and http://www.w3.org/TR/sparql11-results-json/
    if   self._results.get('boolean', None) is not None:
       yield self._results['boolean']
    elif self._results.get('head'):
      cols = self._results.get('head')['vars']
      rows = self._results.get('results', {}).get('bindings', [ ])
      if self._header: yield cols
      for r in rows:
        if self._html: yield [ self._add_html(r[c]) for c in cols ]
        else:          yield [                r[c]  for c in cols ]
    else:
      yield self._results
