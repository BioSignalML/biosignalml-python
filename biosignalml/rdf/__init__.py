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

'''
A generic interface to some RDF library.

We use the RDFlib package from https://github.com/RDFLib/rdflib.

'''

__all__ = [ 'Format', 'NS', 'Uri', 'Node', 'Literal',
            'BlankNode', 'Resource', 'QueryResults', 'Graph' ]

import sys
import uuid
import logging

import rdflib
import rdflib.plugins.memory


class RDFParseError(Exception):
#==============================
  '''Errors when parsing RDF'''
  pass


class Format(object):
#====================
  '''Different RDF representation formats.'''
  RDFXML = 'application/rdf+xml'
  TURTLE = 'text/turtle'
  JSON   = 'application/json'

  @staticmethod
  def mimetype(format):
  #--------------------
    '''
    Get the MIME type of a RDF representation.

    :param format: A RDF representation.
    :rtype: str
    '''
    return format

  @staticmethod
  def name(mimetype):
  #-----------------
    """ Get the name of a format from its mimetype."""
    return { Format.RDFXML: 'xml',
             Format.TURTLE: 'turtle',
             Format.JSON:   'json',
           }.get(mimetype, 'xml')

  @staticmethod
  def format(name):
  #-----------------
    """ Get the RDF format from its name."""
    return { 'xml':    Format.RDFXML,
             'turtle': Format.TURTLE,
             'json':   Format.JSON,
           }.get(name, Format.RDFXML)


class Uri(rdflib.term.Identifier):
#=================================
  '''
  We extend the class with an `__add__()` method to allow a new URI to be formed
  by appending a string to an existing one.
  '''

  def __add__(self, s):
  #--------------------
    '''
    Append a string to a URI.

    :rtype: :class:`Uri`
    '''
    return Uri(str(self) + s)

  def make_uri(self, sibling=False, prefix=None):
  #----------------------------------------------
    """
    Generate a unique URI that starts with this URI.

    :param sibling: When set, replace the last component of our URI with unique text.
      The default is to append unique text to our URI.
    :type: bool
    :param prefix: If set, insert between the URI and unique text.
    :type: str
    :return: A unique URI.
    :rtype: Uri
    """
    u = str(self)
    suffix = '%s/%s' % (prefix, uuid.uuid1()) if prefix else str(uuid.uuid1())
    if   u.endswith(('/', '#')): nu = '%s%s'  % (u, suffix)
    elif sibling:
      slash = u.rfind('/')
      hash  = u.rfind('#')
      if hash > slash: nu = '%s#%s' % (u.rsplit('#', 1)[0], suffix)
      else: nu = '%s/%s' % (u.rsplit('/', 1)[0], suffix)
    else: nu = '%s/%s' % (u, suffix)
    return Uri(nu)


class NS(object):
#================
  """
  Provide a Namespace class.

  We can't wrap `rdflib.namespace.Namespace` because it sub-classes
  `unicode` whose method names then restrict our names.
  """
  def __init__(self, base):
  #------------------------
    self._base = unicode(base)

  def __getattr__(self, name):
  #---------------------------
    return Uri(self._base + (name if isinstance(name, basestring) else ''))

  def __str__(self):
  #----------------
    return self._base

  @property
  def prefix(self):
  #----------------
    """Get the namespace's prefix."""
    return self._base


# Generic namespaces:
NAMESPACES = {
  'xsd':  'http://www.w3.org/2001/XMLSchema#',
  'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
  'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
  'owl':  'http://www.w3.org/2002/07/owl#',
  'dct':  'http://purl.org/dc/terms/',
  'time': 'http://www.w3.org/2006/time#',
  'tl':   'http://purl.org/NET/c4dm/timeline.owl#',
  'uome': 'http://www.sbpax.org/uome/list.owl#',
  'prv':  'http://purl.org/net/provenance/ns#',
  'prov': 'http://www.w3.org/ns/prov#',
  }
for prefix, name in NAMESPACES.iteritems():
  setattr(sys.modules[__name__], prefix.upper(), NS(name))


Node = rdflib.term.Node
#======================
''' A Node in a RDF Graph. '''

Node.as_string = lambda self: str(self)
#--------------------------------------
''' Represent a Node as a string. '''

Node.is_resource = lambda self: isinstance(self, rdflib.term.URIRef)
#---------------

Node.is_blank = lambda self: isinstance(self, rdflib.term.BNode)
#------------

Node.is_literal = lambda self: isinstance(self, rdflib.term.Literal)
#--------------


class Literal(rdflib.term.Literal):
#==================================
  '''
  Create a Literal node.

  :param value: The value of the literal.
  :param datatype: The literal's datatype.
  :param language: The literal's language.
  :type language: str
  '''
  def __new__(cls, value, datatype=None, language=None):
  #-----------------------------------------------------
    return rdflib.term.Literal.__new__(cls, value, datatype=datatype, lang=language)

  def as_string(self):
  #-------------------
    '''
    Return the literal as a quoted string with language and datatype attributes.
    '''
    l = ['"""' + str(self.value) + '"""']
    if   self.language: l.append('@' + self.language)
    elif self.datatype: l.append('^^' + self.datatype)
    return ''.join(l)


class BlankNode(rdflib.term.BNode):
#==================================
  '''
  Create a Blank node.

  :param blank: Blank self identifier.
  :type blank: str
  '''
  def __new__(cls, blank=None):
  #----------------------------
    if blank is not None and blank.startswith('nodeID://'):
      blank = str(blank[9:])    ## Tidy Virtuoso blank node identifiers
    return rdflib.term.BNode.__new__(cls, value=blank)

  def as_string(self):
  #-------------------
    return '_:%s' % unicode(self)


class Resource(rdflib.term.URIRef):
#==================================
  '''
  Create a Resource node.

  :param uri: The URI of the resource.
  '''
  def __new__(cls, uri, **kwds):
  #------------------------------
    return rdflib.term.URIRef.__new__(cls, uri)

  def __init__(self, uri, label='', desc=''):
  #------------------------------------------
    self._label = label
    self._description = desc

  def as_string(self):
  #-------------------
    return self.label if self.label else unicode(self)

  @property
  def label(self):
  #---------------
    return getattr(self, '_label', '')

  @property
  def description(self):
  #---------------------
    return getattr(self, '_description', '')

  @classmethod
  def uuid_urn(cls):
  #-----------------
    '''
    Generate a URN resource in the UUID namespace.
    '''
    return cls('urn:uuid:%s' % uuid.uuid1())

  @staticmethod
  def is_uuid_urn(this):
  #---------------------
    '''
    Check if a resource is a URN in the UUID namespace.

    This is implemented as a static method so we can use it
    to test generic resources.
    '''
    return (isinstance(this, rdflib.term.URIRef)
        and str(this).startswith('urn:uuid:'))

rdflib.term.URIRef.uri = property(lambda self: unicode(self))


class Statement(list):
#=====================
  '''
  The main means of manipulating statements is by the `subject`, `predicate` and `object` properties.
  '''
  def __init__(self, s=None, p=None, o=None, **kwds):
  #------------------------------------------------
    if (s and not isinstance(s, rdflib.term.URIRef)
          and not isinstance(s, rdflib.term.BNode)): s = Resource(s)
    if p and not isinstance(p, rdflib.term.URIRef): p = Resource(p)
    if (o and not isinstance(o, rdflib.term.URIRef)
          and not isinstance(o, rdflib.term.BNode)
          and not isinstance(o, rdflib.term.Literal)): o = Literal(o)
    list.__init__(self, [s, p, o])

  @property
  def subject(self):
  #-----------------
    return self[0]

  @property
  def predicate(self):
  #-------------------
    return self[1]

  @property
  def object(self):
  #----------------
    return self[2]


QueryResults = rdflib.query.Result
#===========


class IOMemory(rdflib.plugins.memory.IOMemory):
#==============================================

  def __obj2id(self, obj):        # Class name is IOMemory to ensure
  #-----------------------        # private metod is overriden.
    """encode object, storing it in the encoding map if necessary,
       and return the integer key"""

    if isinstance(obj, rdflib.term.BNode):
      s = "_:%s" % unicode(obj)
    elif isinstance(obj, rdflib.term.Literal):
      v = ['"""' + unicode(obj.value) + '"""']
      if   obj.language: v.append('@' + unicode(obj.language))
      elif obj.datatype: v.append('^^' + unicode(obj.datatype))
      s = "".join(v)
    elif isinstance(obj, rdflib.term.URIRef):
      s = "<%s>" % unicode(obj)
    else:
      s = obj
    if s not in self.__obj2int:
      id = rdflib.plugins.memory.randid()
      while id in self.__int2obj:
        id = rdflib.plugins.memory.randid()
      self.__obj2int[s] = id
      self.__int2obj[id] = obj
      return id
    return self.__obj2int[s]


class Graph(rdflib.graph.Graph):
#===============================
  '''
  We store graphs in memory.
  '''
  def __init__(self, uri=None):
  #----------------------------
    super(Graph, self).__init__(store=IOMemory(), identifier=uri)

  @property
  def uri(self):
  #-------------
    return self.identifier

  @uri.setter
  def uri(self, value):
  #--------------------
    self.__identifier = value

  @classmethod
  def create_from_resource(cls, uri, format=Format.RDFXML, base=None):
  #-------------------------------------------------------------------
    """
    Create a new Graph from RDF statements in a resource.

    :param uri: The URI of RDF content to parse and add.
    :param format: The content's RDF format.
    :param base: An optional base URI of the content.
    :rtype: A :class:`Graph`
    """
    self = cls(uri)
    self.parse(source=uri, format=Format.name(format), publicID=base)
    return self

  @classmethod
  def create_from_string(cls, uri, string, format=Format.RDFXML):
  #--------------------------------------------------------------
    """
    Create a new Graph from RDF statements in a string.

    :param uri: The URI of the resulting graph. This is also
      use as the base URI when parsing.
    :param string: The RDF to parse and add.
    :type string: str
    :param format: The string's RDF format.
    :rtype: A :class:`Graph`
    """
    self = cls(uri)
    self.parse(data=string, format=Format.name(format), publicID=str(uri))
    return self

  def __str__(self):
  #-----------------
    return str(self.uri)

  def parse_resource(self, uri, format=Format.RDFXML, base=None):
  #--------------------------------------------------------------
    """
    Add statements to the graph from a resource.

    :param uri: The URI of RDF content to parse and add.
    :param format: The content's RDF format.
    :param base: An optional base URI of the content.
    """
    self.parse(source=uri, format=Format.name(format), publicID=base)

  def parse_string(self, string, format=Format.RDFXML, base=None):
  #---------------------------------------------------------------
    """
    Add statements to the graph from a string.

    :param string: The RDF to parse and add.
    :type string: str
    :param format: The string's RDF format.
    :param base: The base URI of the content.
    """
    self.parse(data=string, format=Format.name(format), publicID=base)

  def serialise(self, format=Format.RDFXML, base=None, prefixes={}):
  #-----------------------------------------------------------------
    '''
    Serialise the graph as a string of RDF statements.

    :param format: The RDF format to return.
    :param base: An optional base URI.
    :param prefixes: A dictionary of { 'prefix': 'namespace_uri' } abbreviations
      to use in the resulting serialisation.
    :type prefixes: dict
    :return: The graph serialised as a string.
    :rtype: str
    '''
    if base is None: base = self.uri
    for prefix, uri in prefixes.iteritems():
      self.bind(prefix, uri)
    return self.serialize(format=Format.name(format)) ## BUG IN RDFLIB..., base=base)

#  def __iter__(self):
#  #------------------
#    return self.as_stream(self._default_graph).__iter__()

  def add_statements(self, statements):
  #------------------------------------
    '''
    Add statements to the graph.

    :param statements: A sequence of :class:`Statement`\s to add.
    :type statements: iterator
    '''
    for s in statements: self.add(s)

  def append_graph(self, graph):
  #-----------------------------
    '''
    Add statements from another graph to this graph.

    :param graph: A :class:`Graph` containing statements.
    '''
    if graph is not None:
      for s in graph: self.add(s)

  def contains(self, statement):
  #-----------------------------
    '''
    Test if a statement is in the graph.

    :param statement: The statement to check. Some or all of the `subject`,
      `predicate` or `object` attributes can be `None`, meaning they match any value.
    :type statement: :class:`Statement`
    :return: True if the graph contains `statement`.
    :rtype: bool
    '''
    return statement in self

  def has_resource(self, uri, rtype):
  #----------------------------------
    '''
    Does the graph contain a resource of the given type?
    '''
    return self.contains(Statement(uri, RDF.type, rtype))

  def get_statements(self, statement):
  #-----------------------------------
    '''
    Get all matching statements in the graph.

    :param statement: The statement to find. Some or all of the `subject`,
      `predicate` or `object` attributes can be `None`, meaning they match any value.
    :type statement: :class:`Statement`
    :return: A sequence of :class:`Statement`\s.
    '''
    for s in self.triples(statement): yield Statement(*s)

  def get_object(self, s, p):
  #--------------------------
    '''
    Get the object of a (`subject`, `predicate`) pair. One or both of `subject`
    and `predicate` may be `None`, meaning they match any value.

    :param s: The `subject` of the statement.
    :param p: The `predicate` of the statement.
    :return: The `object` node if the statement (`subject`, `predicate`, `object`) is
      in the graph, otherwise `None`.
    :rtype: :class:`Node`
    '''
    return tuple(self.get_objects(s, p))[0]

  def get_literal(self, s, p):
  #----------------------------
    '''
    Get the object of a (`subject`, `predicate`) pair as a string if it is a
    :class:`Literal`. One or both of `subject` and `predicate` may be `None`,
    meaning they match any value.

    :param s: The `subject` of the statement to lookup.
    :param p: The `predicate` of the statement to lookup.
    :return: The `object` as a string if the statement (`subject`, `predicate`, `object`)
      is in the graph and `object` is a :class:`Literal`; as a :class:`Node` if it
      exists and is not a Literal; otherwise `None`.
    '''
    l = self.get_object(s, p)
    return l.as_string() if l else None

  def get_subjects(self, p, o):
  #----------------------------
    '''
    Get a sequence of subjects matching the pair (`predicate`, `object`). One or
    both of `predicate` and `object` may be `None`, meaning they match any value.

    :param p: The `predicate` of the statement to lookup.
    :param o: The `object` of the statement to lookup.
    :return: An iterator yielding a sequence of `subject` nodes with
      (`subject`, `predicate`, `object`) statements in the graph.
    :rtype: iterator
    '''
    if p and not isinstance(p, rdflib.term.URIRef): p = Resource(p)
    return self.subjects(predicate=p, object=o)

  def get_objects(self, s, p):
  #---------------------------
    '''
    Get a sequence of objects matching the pair (`subject`, `predicate`). One or
    both of `subject` and `predicate` may be `None`, meaning they match any value.

    :param s: The `subject` of the statement to lookup.
    :param p: The `predicate` of the statement to lookup.
    :return: An iterator yielding a sequence of `object` nodes with
      (`subject`, `predicate`, `object`) statements in the graph.
    :rtype: iterator
    '''
    if s and not isinstance(s, rdflib.term.URIRef): s = Resource(s)
    if p and not isinstance(p, rdflib.term.URIRef): p = Resource(p)
    return self.objects(subject=s, predicate=p)

  def get_literals(self, s, p):
  #------------------------------
    '''
    Get a sequence of objects matching the pair (`subject`, `predicate`), with the
    `object` as a string if it is a :class:`Literal`. One or both of `subject`
    and `predicate` may be `None`, meaning they match any value.

    :param s: The `subject` of the statement to lookup.
    :param p: The `predicate` of the statement to lookup.
    :return: An iterator yielding a sequence of strings and non-Literal :class:`Node`\s
       for `object`\s with (`subject`, `predicate`, `object`) statements in the graph.
    :rtype: iterator
    '''
    for v in self.get_objects(s, p): yield v.as_string()

  def set_subject_property(self, s, p, o):
  #---------------------------------------
    """
    Append the statement (s, p, o) to the graph after first removing
    all statements with subject `s` and predicate `p`.
    """
    self.remove(Statement(s, p, None))
    self.add(Statement(s, p, o))

  def query(self, sparql):
  #-----------------------
    '''
    Perform a SPARQL query against RDF statements in the graph.

    :param sparql: The SPARQL query.
    :type: str
    :return: An iterator of the results from the query.
    :rtype: :class:`QueryResults`
    '''
    try:
      return super(Graph, self).query(sparql)
    except Exception, msg:
      logging.error('Graph query: %s', msg)
    return [ ]


######################################################################################
#
# From: http://rdflib.readthedocs.org/en/4.1.0/intro_to_sparql.html
#
#   RDFLib lets you prepare queries before execution, this saves re-parsing and
#   translating the query into SPARQL Algebra each time.
#
#   The method rdflib.plugins.sparql.prepareQuery() takes a query as a string and
#   will return a rdflib.plugins.sparql.sparql.Query object. This can then be passed
#   to the rdflib.graph.Graph.query() method.
#
#   The initBindings kwarg can be used to pass in a dict of initial bindings:
#
######################################################################################


if __name__ == '__main__':
#=========================

  graph_uri = 'http://devel.biosignalml.org/test'
  g = Graph(graph_uri)
  statements = ([Resource(u'http://devel.biosignalml.org/test'),
                   Resource(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                     Resource(u'http://www.biosignalml.org/ontologies/2011/04/biosignalml#Recording')],
                [Resource(u'http://devel.biosignalml.org/test'),
                   Resource(u'http://purl.org/NET/c4dm/timeline.owl#timeline'),
                     Resource(u'http://devel.biosignalml.org/test/timeline')],
                [Resource(u'http://devel.biosignalml.org/test/timeline'),
                   Resource(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                     Literal(u'http://purl.org/NET/c4dm/timeline.owl#RelativeTimeLine')],
                [Resource(u'http://devel.biosignalml.org/test'),
                   Resource(u'http://purl.org/dc/terms/format'),
                     Literal(u'application/x-bsml')],
               )
  g.add_statements(statements)

#  for s in g: print s
  print g.serialize(format="turtle") # , xml_base=graph_uri)
