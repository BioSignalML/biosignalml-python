######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: bbd3c04 on Wed Jun 8 16:47:09 2011 +1200 by Dave Brooks $
#
######################################################


import RDF as librdf
import logging


class NS(librdf.NS):
#===================
  pass


class Uri(librdf.Uri):
#=====================

  def __add__(self, s):
  #--------------------
    return Uri(str(self) + s)


class Node(librdf.Node):
#=======================
  pass


class Literal(Node):
#===================

  def __init__(self, value, datatype=None, language=None):
  #-------------------------------------------------------
    super(Literal, self).__init__(literal=str(value), datatype=Uri(datatype), language=language)

  def __str__(self):
  #-----------------
    l = ['"""' + self._literal[0] + '"""']
    if   self._literal[1]: l.append('@' + self._literal[1])
    elif self._literal[2]: l.append('^^' + self._literal[2])
    return ''.join(l)


class BlankNode(Node):
#=====================

  def __init__(self, blank=None):
  #------------------------------
    super(BlankNode, self).__init__(blank=blank)

  def __str__(self):
  #-----------------
    return '_:%s' % self.blank_identifier


class Resource(Node):
#====================

  def __init__(self, uri):
  #-----------------------
    if isinstance(uri, librdf.Node) and uri.is_resource():
      super(Resource, self).__init__(node=uri)
    else:
      super(Resource, self).__init__(uri=Uri(uri))


class Statement(librdf.Statement):
#=================================
  pass


class Graph(librdf.Model):
#=========================

  def __init__(self, uri=None):
  #----------------------------
    if uri and not isinstance(uri, Node) and not isinstance(uri, Uri):
      uri = Uri(uri)
    self.uri = uri
    super(Graph, self).__init__(storage=librdf.Storage(name='triples',
                                                    storage_name='hashes',
                                                    options_string="hash-type='memory'"))
  def __str__(self):
  #-----------------
    return str(self.uri)

  def parse(self, uri, format, base=None):
  #---------------------------------------
    parser = librdf.Parser(name=str(format))
    try:
      statements = parser.parse_as_stream(uri, base)
      if statements: self.add_statements(statements)
      else:          raise Exception('Error parsing librdf')
    except Exception, msg:
      raise Exception(msg)

  def parse_string(self, string, format, base):
  #--------------------------------------------
    parser = librdf.Parser(name=str(format))
    try:
      statements = parser.parse_string_as_stream(string, base)
      if statements: self.add_statements(statements)
      else:          raise Exception('Error parsing librdf')
    except Exception, msg:
      raise Exception(msg)

  def serialise(self, format='turtle', base=None, prefixes={}):
  #------------------------------------------------------------
    serialiser = librdf.Serializer(format)
    for prefix, uri in prefixes.iteritems():
      serialiser.set_namespace(prefix, Uri(uri))
    return serialiser.serialize_model_to_string(self, base_uri=base)

#  def __iter__(self):
#  #------------------
#    return self.as_stream(self._defaulkt_graph).__iter__()


  def add_statements(self, statements):
  #------------------------------------
    for s in statements: self.append(s)

  def contains(self, statement):
  #-----------------------------
    return super(Graph, self).contains_statement(statement)

  def get_statements(self, statement):
  #-----------------------------------
    return super(Graph, self).find_statements(statement)


  @staticmethod
  def make_literal(node, default):
  #-------------------------------
    return (node.literal_value['string'] if node and node.is_literal()
      else default if default is not None    ### ?????
      else node)                             ### what about str(node) ??

  def get_property(self, s, p):
  #----------------------------
##    node = self.get_target(source, property)
##    return (Node(Uri(node.literal_value['string'])) if node and node.is_literal() else node)
    if s and not isinstance(s, Node) and not isinstance(s, Uri): s = Uri(s)
    if p and not isinstance(p, Node) and not isinstance(p, Uri): s = Uri(p)
    return self.get_target(s, p)

  def get_literal(self, s, p):
  #----------------------------
    return self.make_literal(self.get_property(s, p), None)


  def get_properties(self, s, p):
  #------------------------------
    if s and not isinstance(s, Node) and not isinstance(s, Uri): s = Uri(s)
    if p and not isinstance(p, Node) and not isinstance(p, Uri): s = Uri(p)
    for v, g in self.get_targets_context(s, p): yield (v, g)

  def get_literals(self, s, p):
  #------------------------------
    for v, g in self.get_properties(s, p): yield (self.make_literal(v, None), g)

  def query(self, sparql):
  #-----------------------
    try:
      return librdf.Query(sparql, query_language='sparql11-query').execute(self)
    except Exception, msg:
      logging.error('Graph query: %s', msg)
    return [ ]
