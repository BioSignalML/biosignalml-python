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
import json

from biosignalml import BSML
import biosignalml.model as model
from biosignalml.model.mapping import PropertyMap
from biosignalml.utils import xmlescape

from biosignalml.rdf import RDF, DCT, PRV, XSD
from biosignalml.rdf import Uri, Node, Resource, BlankNode, Graph, Statement
from biosignalml.rdf import Format
import biosignalml.rdf.sparqlstore as sparqlstore

import biosignalml.utils as utils

__all__ = [ 'GraphStore', 'GraphUpdate' ]


PROVENANCE_PATH = '/provenance'     #: Relative to a graph store's URI


class DataItem(model.core.AbstractObject):
#=========================================
  metaclass = PRV.DataItem
  attributes = [ 'type', 'createdby', 'subject', 'precededby' ]
  mapping = { 'createdby':  PropertyMap(PRV.createdBy, subelement=True),
              'subject':    PropertyMap(DCT.subject),
              'precededby': PropertyMap(PRV.precededBy),
              'type':       PropertyMap(RDF.type) }

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    self = cls(uri, None, **kwds)
    self.add_metadata(graph)
    if self.createdby is not None:
      self.createdby = DataCreation.create_from_graph(self.createdby, graph)

    self.followedby = None
    for s in graph.get_subjects(PRV.precededBy, self.uri):
      self.followedby = s
      break

    return self


class DataCreation(model.core.AbstractObject):
#=============================================
  metaclass = PRV.DataCreation
  attributes = [ 'performedby', 'completed' ]
  mapping = { 'performedby': PropertyMap(PRV.performedBy),
              'completed':   PropertyMap(PRV.completedAt, XSD.dateTime,
                                                 utils.datetime_to_isoformat,
                                                 utils.isoformat_to_datetime) }

class GraphStore(object):
#========================
  '''
  An RDF repository storing triples in named graphs with provenance.

  :param base_uri: The URI of the store.
  :param graphtype: The class of graphs for we manage provenance for.
  :param sparqlstore: The :class:`~biosignalml.rdf.sparqlstore.SparqlStore` in which RDF is stored.
  '''
  def __init__(self, base_uri, graphtype, sparqlstore):
  #----------------------------------------------------
    self.uri = Uri(base_uri)
    self._graphtype = graphtype
    self._sparqlstore = sparqlstore
    self._provenance_uri = self.uri + PROVENANCE_PATH

  @property
  def store(self):
  #---------------
    return self._sparqlstore

  @property
  def provenance_uri(self):
  #------------------------
    return self._provenance_uri

  def has_provenance(self, graph_uri):
  #-----------------------------------
    ''' Check a URI is that of a graph for which we have current provenance.'''
    return self._sparqlstore.ask(
      '''graph <%(pgraph)s> { <%(graph)s> a <%(gtype)s> MINUS { [] prv:precededBy <%(graph)s> }}
         graph <%(graph)s> { [] a [] }''',
      params=dict(pgraph=self._provenance_uri, graph=graph_uri, gtype=self._graphtype),
      prefixes=dict(bsml=BSML.prefix, prv=PRV.prefix))


  def get_provenance(self, graph_uri):
  #-----------------------------------
    ''' Return the provenance of a graph.'''
    rdf = self._sparqlstore.construct('<%(uri)s> ?p ?o . ?cr ?cp ?co . ',
            '''graph <%(pgraph)s> { <%(uri)s> a <%(gtype)s> . <%(uri)s> ?p ?o .
                                    <%(uri)s> prv:createdBy ?cr . ?cr ?cp ?co .
                                    optional { ?ltr prv:precededBy <%(uri)s> } }''',
            params=dict(pgraph=self._provenance_uri, uri=graph_uri, gtype=self._graphtype),
            prefixes=dict(prv=PRV.prefix), format=Format.RDFXML)
    return DataItem.create_from_string(graph_uri, rdf, Format.RDFXML)


  def get_resources(self, rtype, rvars='?r', condition='',
                                 group=None, prefixes=None, graph=None, order=None, resource=None):
  #------------------------------------------------------------------------------------------------
    """
    Find resources of the given type and the most recent graphs that hold them.

    The resources found can be restricted by an optional SPARQL graph pattern.

    :param rtype: The type of resource to find. The SPARQL variable used for the
       resource is the first of the `rvars`.
    :param str rvars: Space separated SPARQL variables identifying the resource
       in the query along with any other variables to return values of. The first variable
       is usually that of the resource. Optional, defaults to `?r` unless `resource` is given.
    :param str condition: A SPARQL graph pattern for selecting resources. Optional.
    :param str group: Variables to group the results by. Optional.
    :param dict prefixes: Optional namespace prefixes for the SPARQL query.
    :param graph: The URI of a specific graph to search in, instead of finding
       the most recent. Optional.
    :param str order: The sort order of the SPARQL query. Optional.
    :param str resource: The SPARQL variable of the resource, if not in the `rvars` list.
       Optional.
    :return: A list of (graph_uri, resource_uri, optional_variable) tuples.
    :rtype: list[tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)]
    """
    pfxdict = dict(bsml=BSML.prefix, prv=PRV.prefix)
    if prefixes: pfxdict.update(prefixes)
    varlist = [ var for var in rvars.split() if var[0] == '?' ]
    retvars = [ var[1:] for var in varlist ]
    if resource is None: resource = varlist[0]
    gv = sparqlstore.get_result_value   ## Shorten code
    NOVALUE = { 'value': None }  # For optional result variables
    if order is None: order = ' '.join(varlist)
    if graph is None:
      return [ (gv(r, 'g'), gv(r, retvars[0])) + tuple([gv(r, v) for v in retvars[1:]])
        for r in self.select('?g %(rvars)s',
          '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
             graph ?g { { %(res)s a <%(rtype)s> . %(cond)s } }''',
          params=dict(pgraph=self._provenance_uri, gtype=self._graphtype,
                      res=resource, rtype=rtype, rvars=rvars, cond=condition),
          prefixes=pfxdict,
          group=group,
          order='?g %s' % order)
        ]
    else:
      return [ (Uri(str(graph)), gv(r, retvars[0])) + tuple([gv(r, v) for v in retvars[1:]])
        for r in self.select('%(rvars)s', '{ %(res)s a <%(rtype)s> . %(cond)s }',
          params=dict(res=resource, rtype=rtype, rvars=rvars, cond=condition),
          prefixes=pfxdict,
          graph=graph,
          order=order)
        ]

  def has_resource(self, uri, rtype=None, graph_uri=None):
  #-------------------------------------------------------
    '''
    Is there some graph containing a resource, optionally of the given type?
    '''
    if rtype is None: rtype = '[]'
    else:             rtype = '<%s>' % rtype
    if graph_uri is None:
      return self._sparqlstore.ask(
        '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
           graph ?g { <%(uri)s> a %(rtype)s }''',
        params=dict(pgraph=self._provenance_uri, gtype=self._graphtype, uri=uri, rtype=rtype),
        prefixes=dict(prv=PRV.prefix))
    else:
      return self._sparqlstore.ask(
        '''graph <%(graph)s> { <%(uri)s> a %(rtype)s }''',
        params=dict(graph=graph_uri, uri=uri, rtype=rtype),
        prefixes=dict(prv=PRV.prefix))

  def has_graph(self, uri):
  #------------------------
    '''
    Is there a graph wuth the given URI?
    '''
    return self._sparqlstore.ask('graph <%(pgraph)s> { <%(uri)s> a <%(gtype)s> }',
      params=dict(pgraph=self._provenance_uri, uri=uri, gtype=self._graphtype))

  def get_graph(self, graph_uri, rtype=None):
  #------------------------------------------
    rdf = self._sparqlstore.construct('?s ?p ?o', graph=graph_uri, format=Format.RDFXML)
    ## Virtuoso has a MaxRows limit in its INI file with a default of 10000.
    ## This has been increased to 50000
    resource = Graph.create_from_string(graph_uri, rdf, Format.RDFXML)
    return resource if rtype is None or resource.contains(Statement(None, RDF.type, rtype)) else None

  def get_resource_as_graph(self, uri, rtype, graph_uri=None):
  #-----------------------------------------------------------
    if graph_uri is None:
      graph_uri = uri
      ### Following can give an error from Virtuoso...
      rdf = self._sparqlstore.construct('<%(uri)s> ?p ?o',
              '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
                 graph ?g { <%(uri)s> a <%(rtype)s> ; ?p ?o }''',
              params=dict(pgraph=self._provenance_uri, gtype=self._graphtype, uri=uri, rtype=rtype),
              prefixes=dict(prv=PRV.prefix), format=Format.RDFXML)
    else:
      rdf = self._sparqlstore.construct('<%(uri)s> ?p ?o',
              '<%(uri)s> a <%(rtype)s> ; ?p ?o',
              params=dict(uri=uri, rtype=rtype),
              graph=graph_uri, format=Format.RDFXML)
    resource = Graph.create_from_string(graph_uri, rdf, Format.RDFXML)
    return resource if resource.contains(Statement(uri, RDF.type, rtype)) else None

  def get_resource_graph_uri(self, uri):
  #-------------------------------------
    for r in self.select('?g',
      '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
         graph ?g { <%(uri)s> a [] }''',
        params=dict(pgraph=self._provenance_uri, gtype=self._graphtype, uri=uri),
        prefixes=dict(prv=PRV.prefix)):
      return sparqlstore.get_result_value(r, 'g')

  def query(self, sparql, header=False):
  #-------------------------------------
    return QueryResults(self._sparqlstore, sparql, header)

  def construct(self, template, where=None, params=None, graph=None, format=Format.RDFXML, prefixes=None):
  #-------------------------------------------------------------------------------------------------------
    return self._sparqlstore.construct(template, where, params, graph, format, prefixes)

  def ask(self, query, graph):
  #---------------------------
    return self._sparqlstore.ask(query, graph)

  def select(self, fields, where, **kwds):
  #---------------------------------------
    return self._sparqlstore.select(fields, where, **kwds)


  def get_subjects(self, prop, obj, graph=None, ordered=False):
  #------------------------------------------------------------
    """
    Get subjects of all statements that match a given predicate/object.
    """
    if isinstance(obj, Resource) or isinstance(obj, Uri):
      obj = '<%s>' % obj
    elif not isinstance(obj, Node):
      obj = '"%s"' % obj
    return [ sparqlstore.get_result_value(r, 's')
      for r in self.select('?s', '?s <%(prop)s> %(obj)s',
        params = dict(prop=prop, obj=obj), graph = graph, order = '?s' if ordered else None) ]

  def get_objects(self, subj, prop, graph=None, ordered=False):
  #------------------------------------------------------------
    """
    Get objects of all statements that match a given subject/predicate.
    """
    return [ sparqlstore.get_result_value(r, 'o')
      for r in self.select('?o', '<%(subj)s> <%(prop)s> ?o',
        params = dict(subj=subj, prop=prop), graph = graph, order = '?s' if ordered else None) ]


  def get_types(self, uri, graph=None):
  #------------------------------------
    return self.get_objects(uri, RDF.type, graph)

  def describe(self, uri, graph=None, format=Format.RDFXML):
  #---------------------------------------------------------
    return self._sparqlstore.describe(uri, graph=graph, format=format)

    """
    def description(uri, format):
    #----------------------------
      return self._sparqlstore.construct('?s ?p ?o',
                             '?s ?p ?o FILTER (?s = <%(uri)s> || ?o = <%(uri)s>)',
                             params=dict(uri=uri), graph=graph, format=format)

    class Closure(Graph):
    #--------------------
      def __init__(self, rdf, base, format, store):
        Graph.__init__(self)
        self._base = base
        self._store = store
        self._urns = set()
        for stmt in Graph.create_from_string(base, rdf, format):
          self.append(stmt)
          self.add_urn(stmt.subject)
          self.add_urn(stmt.object)

      def add_urn(self, node):
        if str(node) not in self._urns:
          if Resource.is_uuid_urn(node):
            ttl = description(node, Format.TURTLE)
            self._urns.add(str(node))
            for stmt in Graph.create_from_string(self._base, ttl, Format.TURTLE):
              self.append(stmt)
              ##print '[%s, %s, %s]' % (stmt.subject, stmt.predicate, stmt.object)
              if node != stmt.subject: self.add_urn(stmt.subject)
              if node != stmt.object: self.add_urn(stmt.object)
#          else:
#            for t in self._store.get_types(node, graph):
#              self.append(Statement(node, RDF.type, t))

    rdf = description(uri, Format.RDFXML) # Virtuoso returns bad Turtle typed literals...
    return Closure(rdf, self.uri, Format.RDFXML, self).serialise(format, base = self.uri + '/')  # Need '/' for Tabulator...
    """


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


class QueryResults(object):
#==========================

  def __init__(self, sparqlstore, sparql, header=False):
  #-----------------------------------------------------
    self._base = None
    self._set_prefixes(sparql)
    self._header = header
    #logging.debug('SPARQL: %s', sparql)
    try:
      self._results = json.loads(sparqlstore.query(sparql, Format.JSON))
    except Exception, msg:
      self._results = { 'error': str(msg) }

  @property
  def base(self):
  #--------------
    return self._base

  def _set_prefixes(self, sparql):
  #-------------------------------
    self._prefixes = { }   ### Start with a copy of standard prefixes...
    header = SparqlHead.parse(sparql)
    for h in header:
      if h[0] == 'base':
        self._base = h[1]
      else:       # 'prefix'
        self._prefixes[h[1][0]] = h[1][1]
    #logging.debug('PFX: %s', self._prefixes)

  def abbreviate_uri(self, uri):
  #-----------------------------
    uri = str(uri)
    for name, prefix in self._prefixes.iteritems():
      if uri.startswith(prefix): return '%s:%s' % (name, uri[len(prefix):])
    return uri

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
        yield { c: sparqlstore.get_result_value(r, c) for c in cols }
    else:
      yield self._results



class GraphUpdate(GraphStore):
#=============================

  def insert_triples(self, graph_uri, triples, prefixes=None):
  #-----------------------------------------------------------
    self._sparqlstore.insert_triples(graph_uri, triples, prefixes)

  def replace_graph(self, uri, rdf, format=Format.RDFXML):
  #-------------------------------------------------------
    #### graph.append(Statement(graph.uri, DCT._provenance, self._provenance.add(graph.uri)))

    # If graph already present then rename (to new uuid()) and add
    # provenance...

    # add version statement to graph ??
    # What about actual recording file(s)? They should also be renamed...

    self._sparqlstore.replace_graph(uri, rdf, format=format)

    #  Generate provenance....
    #for k, v in provenance.iter_items():
    #  self._provenance.add(self.uri, content-type, hexdigest, ...)
    #self._sparqlstore.insert(self._provenace, triples...)


  def extend_graph(self, uri, rdf, format=Format.RDFXML):
  #---------------------------------------------------
    self._sparqlstore.extend_graph(uri, rdf, format=format)

  def delete_graph(self, uri):
  #---------------------------
    self._sparqlstore.delete_graph(uri)
    #self._provenance.delete_graph(uri)
    ## Should this set provenance...

  def add_resource_graph(self, uri, rtype, rdf, creator, format=Format.RDFXML):
  #----------------------------------------------------------------------------
    current = self.get_resources(rtype, condition='filter(?r = <%s>)' % uri)
    predecessor = current[0][0] if current else None
    #print "Preceeded by", predecessor
    graph_uri = self.uri.make_uri()
    prov = DataItem(graph_uri, type=self._graphtype,
      subject=uri, precededby=predecessor,
      createdby=DataCreation(self.uri.make_uri(), performedby=creator,
                             completed=utils.utctime() ))
    self.extend_graph(self._provenance_uri, prov.metadata_as_graph().serialise())
    self.replace_graph(graph_uri, rdf, format=format)
    return graph_uri

  def save_subject_property(self, graph_uri, s, p):
  #------------------------------------------------
    """
    """
    o = getattr(s, p, None)
    ### Following should be done in Mapping class...
    if o not in ['', None] and isinstance(s, model.core.AbstractObject):
      mc = [ c.metaclass for c in s.__class__.__mro__ if c.__dict__.get('metaclass') ]
      for k, m in s.rdfmap.mapping.iteritems():
        if (k[0] is None or k[0] in mc) and k[1] == p:
          if isinstance(o, model.core.AbstractObject): v = "<%s>" % str(o.uri)
          else:
            if m.to_rdf is not None: o = m.to_rdf(o)
            v = '"%s"' % str(o)
            if m.datatype is not None: v += "^^<%s>" % str(m.datatype)
          self._sparqlstore.update_triples(graph_uri,
            [("<%s>" % str(s.uri), "<%s>" % str(m.property), v)])
          return
