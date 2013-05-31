######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
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
Abstract BioSignalML objects.
'''

import logging

import biosignalml.rdf as rdf
from biosignalml.rdf import RDFS, DCT, XSD, PRV
import biosignalml.utils as utils

from .ontology import BSML
from .mapping import Mapping, PropertyMap

__all__ = [ 'AbstractObject' ]


class AbstractObject(object):
#============================
  """
  A general abstract resource with metadata.

  :param uri: URI of the resource,
  :type uri: str, Uri or Resource Node
  :param metadata: Dictionary containing metadata values for the resource.
  :type metadata: dict
  :param kwds: Keyword/value pairs of metadata elements. These have precedence
    over values in the `metadata` parameter for setting of attributes; values
    in the `metadata` parameter take precedence for setting the object's
    `metadata` dictionary.

  Resource properties with names in the :attr:`attributes` list are stored as attributes
  of the class instance; other elements are stored in the :attr:`metadata` dictionary.
  """

  metaclass = None
  '''Class in BioSignalML Ontology as a :class:`~biosignalml.rdf.Resource`'''

  attributes = [ 'uri', 'label', 'comment', 'description', 'precededBy', 'creator', 'created' ]
  '''List of generic attributes all resources have.'''

  mapping = { 'label':       PropertyMap(RDFS.label),
              'comment':     PropertyMap(RDFS.comment),
              'description': PropertyMap(DCT.description),
              'precededBy':  PropertyMap(PRV.precededBy),
              'creator':     PropertyMap(DCT.creator, to_rdf=PropertyMap.get_uri),
              'created':     PropertyMap(DCT.created, datatype=XSD.dateTime,
                                         to_rdf=utils.datetime_to_isoformat,
                                         from_rdf=utils.isoformat_to_datetime),
            }

  rdfmap = None
  '''The :class:`~biosignalml.model.mapping.Mapping` used to map between RDF properties and attributes.'''

  def __new__(cls, *args, **kwds):
  #-------------------------------
    if cls.__dict__.get('rdfmap') is None:
      rdfmap = Mapping()
      for c in reversed(cls.__mro__):
        if c.__dict__.get('mapping'): rdfmap.update(c.metaclass, c.mapping)
      cls.rdfmap = rdfmap
    return object.__new__(cls)


  def __init__(self, uri, metadata=None, **kwds):
  #----------------------------------------------
    self.metadata = AbstractObject.set_attributes(self, **kwds)
    '''Dictionary of property values with names not in :attr:`attributes` list.'''
    if metadata is not None:
      self.metadata.update(AbstractObject.set_attributes(self, **metadata))
    self.uri = (uri     if isinstance(uri, rdf.Uri) or uri is None  # None ==> Blank node
           else uri.uri if isinstance(uri, rdf.Node) and uri.is_resource()
           else rdf.Uri(str(uri).strip()))
    self.node = rdf.BlankNode() if uri is None else rdf.Resource(self.uri)
    self.graph = None

  def __str__(self):
  #-----------------
    try:
      return 'Object[%s]: <%s>' % (self.metaclass, self.node)
    except AttributeError:
      return 'Object[%s]: None' %  self.metaclass

  def __eq__(self, this):
  #----------------------
    return (isinstance(this, AbstractObject)
            and str(self.uri) == str(this.uri)
            and str(self.metaclass.uri) == str(this.metaclass.uri)
         or isinstance(this, rdf.Node) and str(self.uri) == str(this.uri)
         or isinstance(this, rdf.Uri)  and str(self.uri) == str(this)
            )

  def __ne__(self, this):
  #----------------------
    return not self.__eq__(this)

  @staticmethod
  def _equal_values(v1, v2):
  #-------------------------
    # This is an attempt to circimvent an issue with Virtuouso whereby
    # the value of "PT30M6.6S"^^<http://www.w3.org/2001/XMLSchema#dayTimeDuration
    # is seen as two different values, one of
    # "1806.6"^^<http://www.w3.org/2001/XMLSchema#dayTimeDuration, the other of
    # "PT30M6.599999S"^^<http://www.w3.org/2001/XMLSchema#dayTimeDuration
    EPSILON = 10**-9
    try:
      f1 = float(v1)
      f2 = float(v2)
      return f1 == f2 or abs((f1 - f2)/(f1 + f2)) < EPSILON
    except Exception:
      return v1 == v2

  def _assign(self, attr, value, functional=True):
  #-----------------------------------------------
    if attr in self.__dict__:
      v = getattr(self, attr, None)
      if functional or v in [None, '']:
        setattr(self, attr, value)
      elif isinstance(v, set):
        v.add(value)
      elif isinstance(v, list):
        v.append(value)
      elif not self._equal_values(v, value):
        setattr(self, attr, set([v, value]))
    elif attr is not None:
      v = self.metadata.get(attr)
      if functional or v in [None, '']:
        self.metadata[attr] = value
      elif isinstance(v, set):
        v.add(value)
      elif isinstance(v, list):
        v.append(value)
      elif not self._equal_values(v != value):
        self.metadata[attr] = set([v, value])


  def initialise(self, **kwds):
  #----------------------------
    pass

  @classmethod
  def initialise_class(cls, obj, **kwds):
  #--------------------------------------
    if obj.__class__ not in cls.__mro__:
      raise TypeError('Object not in superclasses')
    ## Need to go from cls to obj.class in __mro__ and set
    ## any C.attributes from obj.graph (using C.mapping if defined)
    if hasattr(obj, 'graph'):
      pos = cls.__mro__.index(obj.__class__) - 1
      while pos >= 0:
        for attr in cls.__mro__[pos].__dict__.get('attributes', []):
          v = obj.rdfmap.get_value_from_graph(obj, attr, obj.graph)
          if v is not None:
            setattr(obj, attr, None)    # So it's able to be _assign()ed to
            obj._assign(attr, v)
        pos -= 1
    obj.__class__ = cls
    cls.initialise(obj, **kwds)
    return obj

  def metaclassof(self, metaclass):
  #--------------------------------
    '''
    Check if an object has a given metaclass in its class hierarchy.

    '''
    for cls in self.__class__.__mro__:
      if getattr(cls, 'metaclass', None) == metaclass: return True
    return False

  def set_attributes(self, **values):
  #----------------------------------
    '''
    Set attribute if `key` exists in an :attr:`attributes` list of any class in hierarchy.

    :param values: Dictionary of `{ key: value }` pairs to set as attributes.
    :type values: dict
    :return: A dictionary containing key/value pairs that are not in attributes list.
    '''
    attribs = [ ]
    for cls in self.__class__.__mro__:
      for attr in cls.__dict__.get('attributes', []):
        value = values.get(attr)
        if value is not None:
          if getattr(self, attr, None) is None:    # Only assign if not already set
            setattr(self, attr, value)
        elif attr not in self.__dict__:
          setattr(self, attr, None)                # So it's able to be _assign()ed to
        attribs.append(attr)                      # Attributes that have been set
    return { attr: value for attr, value in values.iteritems()
      if not (value is None or attr in attribs or attr[0] == '_') }


  def set_metadata(self, metadata=None, **kwds):
  #----------------------------------------------
    """
    Update metadata attributes.

    :param metadata: Dictionary containing metadata values for the resource.
    :type metadata: dict
    :param kwds: Keyword/value pairs of metadata elements. These have precedence
      over values in the `metadata` parameter for setting of attributes; values
      in the `metadata` parameter take precedence for setting the object's
      `metadata` dictionary.
    """
    if metadata is not None:
      self.metadata.update(AbstractObject.set_attributes(self, **metadata))
    self.metadata.update(AbstractObject.set_attributes(self, **kwds))


  def get_attributes(self):
  #------------------------
    '''
    Get values of attributes if defined in :attr:`attributes` list of class hierarchy.

    :return: Dictionary of { key: value } pairs of attribute values.
    :rtype: dict
    '''
    metadata = { }
    for cls in self.__class__.__mro__:
      if 'attributes' in cls.__dict__:
        for attr in cls.__dict__['attributes']:
          value = getattr(self, attr, None)
          if value is not None: metadata[attr] = value
    return metadata

  def make_uri(self, sibling=False, prefix=None):
  #----------------------------------------------
    """
    Generate a unique URI that starts with the resource's URI.

    :param sibling: When set, replace the last component of our URI with unique text.
      The default is to append unique text to our URI.
    :type: bool
    :param prefix: If set, insert between the URI and unique text.
    :type: str
    :return: A unique URI.
    :rtype: str
    """
    return self.uri.make_uri(sibling=sibling, prefix=prefix)

  def metadata_as_stream(self):
  #----------------------------
    '''
    Return a stream of RDF statements about ourselves.
    '''
    if self.metaclass:
      yield rdf.Statement(self.node, rdf.RDF.type, self.metaclass)
      for s in self.rdfmap.statement_stream(self): yield s

  def save_to_graph(self, graph):
  #------------------------------
    '''
    Add RDF statements about ourselves to a graph.
    '''
    graph.add_statements(self.metadata_as_stream())

  def metadata_as_graph(self):
  #---------------------------
    """
    Return a RDF graph containing our metadata.
    """
    graph = rdf.Graph(self.uri)
    self.save_to_graph(graph)
    return graph

  def metadata_as_string(self, format=rdf.Format.RDFXML, base=None, prefixes=None):
  #-------------------------------------------------------------------------------
    """
    Return metadata as a serialised RDF string.
    """
    namespaces = { 'bsml': BSML.URI }
    namespaces.update(rdf.NAMESPACES)
    if prefixes: namespaces.update(prefixes)
    return self.metadata_as_graph().serialise(base=base, format=format, prefixes=namespaces)

  def add_metadata(self, graph):
  #-----------------------------
    """
    Set attributes from RDF triples in a graph.

    :param graph: A graph of RDF statements.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    if self.metaclass is not None and graph.contains(rdf.Statement(self.uri, rdf.RDF.type, self.metaclass)):
      for stmt in graph.get_statements(rdf.Statement(self.uri, None, None)):
        for metaclass in [getattr(cls, 'metaclass', None)
                            for cls in self.__class__.__mro__ if cls != object]:
          s, attr, v, fn = self.rdfmap.metadata(metaclass, stmt)
          #logging.debug("%s: %s = '%s'", self.uri, attr, v)  ###
          if attr is not None:
            self._assign(attr, v, fn)
            break

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of a resource, setting attributes from RDF triples in a graph.

    :param uri: The URI for the resource.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`AbstractObject` or a sub-class.
    '''
    self = cls(uri, **kwds)
    self.add_metadata(graph)
    self.graph = graph
    return self

  @classmethod
  def create_from_string(cls, uri, string, format=rdf.Format.RDFXML, **kwds):
  #--------------------------------------------------------------------------
    """
    Create a new instance of a resource, setting attributes from RDF statements in a string.

    :param uri: The URI for the resource.
    :param str string: The RDF to parse and add.
    :param format: The string's RDF format.
    :rtype: :class:`AbstractObject` or a sub-class.
    """
    return cls.create_from_graph(uri, rdf.Graph.create_from_string(uri, string, format), **kwds)

  def set_from_graph(self, attr, graph):
  #-------------------------------------
    '''
    Set an attribute from a RDF statement in the form `(uri, attr, value)`
    contained in a graph.
    '''
    v = self.rdfmap.get_value_from_graph(self.uri, attr, graph)
    if v: self._assign(attr, v)
