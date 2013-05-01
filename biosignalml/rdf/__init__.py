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

We use the Redland RDF Libraries and their Python bindings,
available from http://librdf.org/.

'''

__all__ = [ 'Format', 'NS', 'Uri', 'Node', 'Literal',
            'BlankNode', 'Resource', 'QueryResults', 'Graph' ]

import sys
import uuid
import logging

import RDF as librdf

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
    return { Format.RDFXML: 'rdfxml',
             Format.TURTLE: 'turtle',
             Format.JSON:   'json',
           }.get(mimetype, 'rdfxml')

  @staticmethod
  def format(name):
  #-----------------
    """ Get the RDF format from its name."""
    return { 'rdfxml': Format.RDFXML,
             'turtle': Format.TURTLE,
             'json':   Format.JSON,
           }.get(name, Format.RDFXML)


class NS(librdf.NS):
#===================
  '''
  Wrapper for Redland Namespace utility class --- see http://librdf.org/docs/pydoc/RDF.html#NS.
  '''
  @property
  def prefix(self):
  #----------------
    """Get the namespace's prefix."""
    return self._prefix


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


class Uri(librdf.Uri):
#=====================
  '''
  Wrapper for Redland URI class --- see http://librdf.org/docs/pydoc/RDF.html#Uri.

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


class Node(librdf.Node):
#=======================
  '''
  Wrapper for Redland Node (RDF Resource, Property, Literal)
  class --- see http://librdf.org/docs/pydoc/RDF.html#Node.
  '''

  def as_string(self):
  #-------------------
    return (self.literal_value['string'] if self.is_literal()
      else str(self))            ## Add <...> around str(resource) selfs ??


class Literal(Node):
#===================
  '''
  Create a Literal node.

  :param value: The value of the literal.
  :param datatype: The literal's datatype.
  :param language: The literal's language.
  :type language: str
  '''
  def __init__(self, value, datatype=None, language=None):
  #-------------------------------------------------------
    super(Literal, self).__init__(literal=str(value), datatype=Uri(datatype), language=language)

  def as_string(self):   ## V's __str__ ???
  #-------------------
    '''
    Return the literal as a quoted string with language and datatype attributes.
    '''
    l = ['"""' + self.literal[0] + '"""']
    if   self.literal[1]: l.append('@' + self.literal[1])
    elif self.literal[2]: l.append('^^' + self.literal[2])
    return ''.join(l)


class BlankNode(Node):
#=====================
  '''
  Create a Blank node.

  :param blank: Blank self identifier.
  :type blank: str
  '''
  def __init__(self, blank=None):
  #------------------------------
    if blank is not None and blank.startswith('nodeID://'):
      blank = str(blank[9:])    ## Tidy Virtuoso blank node identifiers
    super(BlankNode, self).__init__(blank=blank)

  def __str__(self):
  #-----------------
    return '_:%s' % self.blank_identifier


class Resource(Node):
#====================
  '''
  Create a Resource node.

  :param uri: The URI of the resource.
  '''
  def __init__(self, uri, label='', desc=''):
  #------------------------------------------
    if isinstance(uri, librdf.Node) and uri.is_resource():
      super(Resource, self).__init__(node=uri)
    else:
      super(Resource, self).__init__(uri=Uri(uri))
    self._label = label
    self._description = desc

  def __str__(self):
  #-----------------
    return self.label if self.label else str(self.uri)

  def __eq__(self, this):
  #----------------------
    return (isinstance(this, librdf.Node) and this.is_resource()
              and str(self.uri) == str(this.uri)
         or isinstance(this, librdf.Uri)
              and str(self.uri) == str(this))

  def __ne__(self, this):
  #----------------------
    return not self.__eq__(this)

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
    return ((isinstance(this, librdf.Node) and this.is_resource()
          or isinstance(this, librdf.Uri)) and str(this).startswith('urn:uuid:'))


class Statement(librdf.Statement):
#=================================
  '''
  Wrapper for Redland Statement (triple) class --- see http://librdf.org/docs/pydoc/RDF.html#Statement.

  The main means of manipulating statements is by the `subject`, `predicate` and `object` properties.
  '''
  def __init__(self, s=None, p=None, o=None, **kwds):
  #--------------------------------------------------
    if s and not isinstance(s, librdf.Node) and not isinstance(s, librdf.Uri): s = Uri(s)
    if p and not isinstance(p, librdf.Node) and not isinstance(p, librdf.Uri): p = Uri(p)
    librdf.Statement.__init__(self, subject=s, predicate=p, object=o, **kwds)


class QueryResults(librdf.QueryResults):
#=======================================
  '''
  Wrapper for Redland QueryResults class.

  The following has been obtained via `pydoc` as the class is not documented
  at http://librdf.org/docs/pydoc/RDF.html.

  .. py:method:: as_stream()

     Return the query results as a stream of triples (RDF.Statement)

  .. py:method:: finished()

     Test if reached the last variable binding result

  .. py:method:: get_binding_name(offset)

     Get the name of a variable binding by offset

  .. py:method:: get_binding_value(offset)

     Get the value of a variable binding by offset

  .. py:method:: get_binding_value_by_name(name)

     Get the value of a variable binding by variable name

  .. py:method:: get_bindings_count()

     Get the number of variable bindings in the query result

  .. py:method:: get_boolean()

     Get the boolean query result

  .. py:method:: is_bindings()

     Test if the query results format is variable bindings

  .. py:method:: is_boolean()

     Test if the query results format is a boolean

  .. py:method:: is_graph()

     Test if the query results format is an RDF graph

  .. py:method:: make_results_hash()

  .. py:method:: to_file(name, format_uri=None, base_uri=None)

     Serialize to filename name in syntax format_uri using the optional base URI.

  .. py:method:: to_string(format_uri=None, base_uri=None)

     Serialize to a string syntax format_uri using the optional base URI.
  '''

  def next(self):
  #--------------
    '''
    Get the next variable binding result.

    We force the resulting Nodes to be an appropriate sub-class.
    '''
    r = super(QueryResults, self).next()
    if isinstance(r, dict):
      for n, v in r.iteritems():
        if   v is None:       pass
        elif v.is_resource(): r[n].__class__ = Resource
        elif v.is_literal():  r[n].__class__ = Literal
        elif v.is_blank():    r[n].__class__ = BlankNode
    return r


class Graph(librdf.Model):
#=========================
  '''
  Extends Redland Model class --- see http://librdf.org/docs/pydoc/RDF.html#Model.

  We always store graphs in memory using a hash index.
  '''
  def __init__(self, uri=None):
  #----------------------------
    librdf.Model.__init__(self, storage=librdf.Storage(name='triples',
                                                       storage_name='hashes',
                                                       options_string="hash-type='memory'"))
    if isinstance(uri, Node): uri = uri.uri
    if uri and not isinstance(uri, Uri): uri = Uri(str(uri))
    self.uri = uri

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
    self.parse_resource(uri, format, base)
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
    self.parse_string(string, format, str(uri))
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
    parser = librdf.Parser(mime_type=format)
    try:
      statements = parser.parse_as_stream(uri, base)
      if statements: self.add_statements(statements)
      else:          raise RDFParseError, 'RDF parsing error'
    except librdf.RedlandError, msg:
      raise RDFParseError, msg

  def parse_string(self, string, format=Format.RDFXML, base=None):
  #---------------------------------------------------------------
    """
    Add statements to the graph from a string.

    :param string: The RDF to parse and add.
    :type string: str
    :param format: The string's RDF format.
    :param base: The base URI of the content.
    """
    parser = librdf.Parser(name=Format.name(format))
    try:
      statements = parser.parse_string_as_stream(string, base)
      if statements: self.add_statements(statements)
      else:          raise RDFParseError, 'RDF parsing error'
    except librdf.RedlandError, msg:
      raise RDFParseError, msg

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
    serialiser = librdf.Serializer(name=Format.name(format))
    for prefix, uri in prefixes.iteritems():
      serialiser.set_namespace(prefix, Uri(uri))
    return serialiser.serialize_model_to_string(self, base_uri=base)

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
    for s in statements: self.append(s)

  def append_graph(self, graph):
  #-----------------------------
    '''
    Add statements from anothe graph to this graph.

    :param graph: A :class:`Graph` containing statements.
    '''
    if graph is not None:
      for s in graph: self.append(s)

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
    return super(Graph, self).contains_statement(statement)

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
    return super(Graph, self).find_statements(statement)

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
##    node = self.get_target(source, property)
##    return (Node(Uri(node.literal_value['string'])) if node and node.is_literal() else node)
    if s and not isinstance(s, librdf.Node) and not isinstance(s, librdf.Uri): s = Uri(s)
    if p and not isinstance(p, librdf.Node) and not isinstance(p, librdf.Uri): p = Uri(p)
    return self.get_target(s, p)

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
    if p and not isinstance(p, librdf.Node) and not isinstance(p, librdf.Uri): p = Uri(p)
    for s in self.get_sources(p, o): yield s

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
    if s and not isinstance(s, librdf.Node) and not isinstance(s, librdf.Uri): s = Uri(s)
    if p and not isinstance(p, librdf.Node) and not isinstance(p, librdf.Uri): p = Uri(p)
    for o in self.get_targets(s, p): yield o

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
    for stmt in self.find_statements(Statement(s, p, None)):
      del self[stmt]
    self.append(Statement(s, p, o))

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
      results = librdf.Query(sparql, query_language='sparql11-query').execute(self)
      results.__class__ = QueryResults
      return results
    except Exception, msg:
      logging.error('Graph query: %s', msg)
    return [ ]
