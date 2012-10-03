######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
######################################################

import logging
import json

import RDF as librdf
from tornado.options import options

from biosignalml import BSML
import biosignalml.model as model
from biosignalml.model.mapping import PropertyMap
from biosignalml.utils import xmlescape

from biosignalml.rdf import RDF, DCTERMS, PRV, XSD
from biosignalml.rdf import Uri, Node, Resource, BlankNode, Graph, Statement
from biosignalml.rdf import Format

import biosignalml.utils as utils


PROVENANCE_PATH = '/provenance'     #: Relative to a graph store's URI


class DataItem(model.core.AbstractObject):
#=========================================
  metaclass = PRV.DataItem
  attributes = [ 'type', 'createdby', 'subject', 'precededby' ]
  mapping = { ('createdby',  None): PropertyMap(PRV.createdBy),
              ('subject',    None): PropertyMap(DCTERMS.subject),
              ('precededby', None): PropertyMap(PRV.precededBy),
              ('type',       None): PropertyMap(RDF.type) }

class DataCreation(model.core.AbstractObject):
#=============================================
  metaclass = PRV.DataCreation
  attributes = [ 'performedby', 'completed' ]
  mapping = { ('performedby', None): PropertyMap(PRV.performedBy),
              ('completed',   None): PropertyMap(PRV.completedAt, XSD.dateTime,
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

  def has_provenance(self, graph_uri):
  #-----------------------------------
    ''' Check a URI is that of a graph for which we have current provenance.'''
    return self._sparqlstore.ask(
      '''graph <%(pgraph)s> { <%(graph)s> a <%(gtype)s> MINUS { [] prv:precededBy <%(graph)s> }}
         graph <%(graph)s> { [] a [] }''',
      params=dict(pgraph=self._provenance_uri, graph=graph_uri, gtype=self._graphtype),
      prefixes=dict(bsml=BSML.prefix))


#  def add_graph(self, graph, rdf, format=rdf.Format.RDFXML):
#  #---------------------------------------------------------
#    self._sparqlstore.extend_graph(graph, rdf, format=format)

#  def replace_graph(self, graph, rdf, format=rdf.Format.RDFXML):
#  #-------------------------------------------------------------
#    self._sparqlstore.replace_graph(graph, rdf, format=format)

#  def delete_graph(self, graph):
  #-----------------------------
    ## 'DCTERMS.dateRemoved' is not a DCTERMS Terms property...
    ## self.append(Statement(graph, DCTERMS.dateRemoved, datetime_to_isoformat(utctime()) ))
    ## ANd need to update the store...
#    self._sparqlstore.delete_graph(graph)
    ## Follow graph with another DataItem that is not of 'graphtype'
#    pass


  def add_resource_graph(self, uri, rtype, rdf, creator, format=Format.RDFXML):
  #----------------------------------------------------------------------------
    current = self.get_resources(rtype, condition='filter(?r = <%s>)' % uri)
    predecessor = current[0] if current else None
    graph_uri = self.uri.make_uri()
    prov = DataItem(graph_uri, type=self._graphtype,
      subject=uri, precededby=predecessor,
      createdby=DataCreation(self.uri.make_uri(), performedby=creator,
                             completed=utils.utctime() ))
    self._sparqlstore.extend_graph(self._provenance_uri, prov.metadata_as_graph().serialise())
    self._sparqlstore.replace_graph(graph_uri, rdf, format=format)


  def get_resources(self, rtype, rvars='?r', condition='', prefixes=None):
  #-----------------------------------------------------------------------
    """
    Find resources of the given type and the most recent graphs that
    hold them.

    The resources found can be restricted by an optional SPARQL graph pattern.

    :param rtype: The type of resource to find.
    :param rvars (str): Space separated SPARQL variables identifying the resource
       in the query along with any other variables to return values of. The first variable
       is assumed to taht of the resource. Optional, defaults to `?r`.
    :param condition (str): A SPARQL graph pattern for selecting resources. Optional.
    :param prefixes (dict): Optional namespace prefixes for the SPARQL query.
    :return: A list of (graph_uri, resource_uri, optional_variable) tuples.
    :rtype: list[tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)]
    """
    pfxdict = dict(bsml=BSML.prefix, prv=PRV.prefix)
    if prefixes: pfxdict.update(prefixes)
    variables = [ var[1:] for var in rvars.split() ]
    NOVALUE = { 'value': None }  # For optional result variables
    return [ (Uri(r['g']['value']), Uri(r[variables[0]]['value']))
              + tuple([r.get(v, NOVALUE)['value'] for v in variables[1:]])
      for r in self._sparqlstore.select('?g %(rvars)s',
        '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
           graph ?g { ?%(rvar)s a <%(rtype)s> . %(cond)s }''',
        params=dict(pgraph=self._provenance_uri, gtype=self._graphtype,
                    rtype=rtype, rvars=rvars, rvar=variables[0], cond=condition),
        prefixes=pfxdict,
        distinct=True,
        order='?g %s' % rvars)
      ]


  def has_resource(self, uri, rtype):
  #----------------------------------
    '''
    Is there some graph containing a resource of the given type?
    '''
    return self._sparqlstore.ask(
      '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
         graph ?g { <%(uri)s> a <%(rtype)s> }''',
      params=dict(pgraph=self._provenance_uri, rtype=rtype, uri=uri, gtype=self._graphtype))


  def get_resource_as_graph(self, uri, rtype, graph_uri=None):
  #-----------------------------------------------------------
    if graph_uri is None:
      ### Following can give an error from Virtuoso...
      rdf = self._sparqlstore.construct('<%(uri)s> ?p ?o',
              '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { [] prv:precededBy ?g }}
                 graph ?g { <%(uri)s> a <%(rtype)s> . <%(uri)s> ?p ?o }''',
              params=dict(pgraph=self._provenance_uri, gtype=self._graphtype, uri=uri, rtype=rtype),
              prefixes=dict(prv=PRV.prefix), format=Format.RDFXML)
    else:
      rdf = self._sparqlstore.construct('<%(uri)s> ?p ?o',
              'graph <%(graph)s> { <%(uri)s> a <%(rtype)s> . <%(uri)s> ?p ?o }',
              params=dict(graph=graph_uri, uri=uri, rtype=rtype), format=Format.RDFXML)

    ## Virtuoso has a MaxRows limit in its INI file with a default of 10000.
    ## This has been increased to 50000
    return Graph.create_from_string(uri, rdf, Format.RDFXML)


  def update(self, uri, triples):
  #------------------------------
    self._sparqlstore.update(uri, triples)


  def replace_graph(self, uri, rdf, format=Format.RDFXML):
  #-------------------------------------------------------
    #### graph.append(Statement(graph.uri, DCTERMS._provenance, self._provenance.add(graph.uri)))

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



  def query(self, sparql, header=False, abbreviate=False, htmlbase=None):
  #----------------------------------------------------------------------
    return QueryResults(self._sparqlstore, sparql, header, abbreviate, htmlbase)



#  def construct(self, template, where, params=None, graph=None, format=Format.RDFXML, prefixes=None):
#  #--------------------------------------------------------------------------------------------------
#    return self._sparqlstore.construct(template, where, params, graph, format, prefixes)


  def ask(self, query, graph):
  #---------------------------
    return self._sparqlstore.ask(query, graph)

  def get_subjects(self, prop, obj, graph, ordered=False):
  #-------------------------------------------------------
    if isinstance(obj, Resource) or isinstance(obj, Uri):
      obj = '<%s>' % obj
    elif not isinstance(obj, Node):
      obj = '"%s"' % obj
    return [ r['s']['value'] for r in
                  self._sparqlstore.select('?s', '?s <%(prop)s> %(obj)s',
                                            params = dict(prop=prop, obj=obj),
                                            graph = graph,
                                            order = '?s' if ordered else None) ]

  def get_objects(self, subj, prop, graph):
  #----------------------------------------
    """
    Get objects of all statements that match a given subject/predicate.
    """
    objects = []
    for r in self._sparqlstore.select('?o', '<%(subj)s> <%(prop)s> ?o',
                                      params = dict(subj = subj, prop=prop),
                                      graph = graph):
      if   r['o']['type'] == 'uri':           objects.append(Resource(Uri(r['o']['value'])))
      elif r['o']['type'] == 'bnode':         objects.append(BlankNode(r['o']['value']))
      elif r['o']['type'] == 'literal':       objects.append(r['o']['value'])
      elif r['o']['type'] == 'typed-literal': objects.append(r['o']['value']) ## check datatype and convert...
    return objects


  def get_types(self, uri, graph):
  #------------------------------
    return self.get_objects(uri, RDF.type, graph)


  def describe(self, uri, graph, format=Format.RDFXML):
  #----------------------------------------------------

    def description(uri, graph, format):
    #-----------------------------------
      return self._sparqlstore.construct('?s ?p ?o',
                             '?s ?p ?o FILTER (?s = <%(uri)s> || ?o = <%(uri)s>)',
                             params=dict(uri=uri), graph=graph, format=format)
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

    rdf = description(uri, graph, format)
    return Closure(rdf, self.uri, format).serialise(format, base = self.uri + '/')  # Need '/' for Tabulator...



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

  def __init__(self, sparqlstore, sparql, header=False, abbreviate=False, htmlbase=None):
  #--------------------------------------------------------------------------------------
    self._set_prefixes(sparql)
    self._header = header
    self._abbreviate = abbreviate
    self._htmlbase = htmlbase
    #logging.debug('SPARQL: %s', sparql)
    try:
      self._results = json.loads(sparqlstore.query(sparql, Format.JSON))
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
      if value.startswith(self._htmlbase):
        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
                       % (LT,
                          '/repository/' + value[len(options.resource_prefix):],
                          value, uri,
                          GT))
############### '/repository/' is web-server path to view objects in repository
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
        if self._htmlbase: yield [ self._add_html(r[c]) for c in cols ]
        else:              yield [                r[c]  for c in cols ]
    else:
      yield self._results
