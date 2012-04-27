######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
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
#  $ID: bbd3c04 on Wed Jun 8 16:47:09 2011 +1200 by Dave Brooks $
#
######################################################
'''
Abstract BioSignalML objects.
'''

import uuid
import logging

import biosignalml.rdf as rdf
from biosignalml import BSML

import mapping


class AbstractObject(object):
#============================
  """
  A general abstract resource with metadata.

  :param uri: URI of the resource,
  :type uri: str
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
  '''Class in BioSignalML Ontology as a :class:`biosignalml.rdf.Resource`'''

  attributes = [ 'uri', 'description' ]
  '''List of generic attributes all resources have.'''

  rdfmap = mapping.Mapping()
  '''The :class:`~biosignalml.model.mapping.Mapping` used to map between RDF properties and attributes.'''


  def __init__(self, uri, metadata=None, **kwds):
  #----------------------------------------------
    self.metadata = AbstractObject.set_attributes(self, **kwds)
    '''Dictionary of property values with names not in :attr:`attributes` list.'''
    if metadata is not None:
      self.metadata.update(AbstractObject.set_attributes(self, **metadata))
    self.uri = rdf.Uri(str(uri).strip())
    self.graph = None

  def __str__(self):
  #-----------------
    return '%s: %s' % (self.__class__, self.uri)

  def initialise(self, *args):
  #---------------------------
    pass

  @classmethod
  def initialise_class(cls, obj, *args):
  #-------------------------------------
    if obj.__class__ not in cls.__mro__:
      raise TypeError('Object not in superclasses')
    ## Need to go from cls to obj.class in __mro__ and set
    ## any C.attributes from obj.graph (using C.mapping if defined)
    if getattr(obj, 'graph', None):
      pos = cls.__mro__.index(obj.__class__) - 1
      while pos >= 0:
        for attr in cls.__mro__[pos].__dict__.get('attributes', []):
          v = cls.rdfmap.get_value_from_graph(obj, attr, obj.graph)
          if v is not None:
            setattr(obj, attr, None)    # So it's able to be _assign()ed to
            obj._assign(attr, v)
        pos -= 1
    obj.__class__ = cls
    cls.initialise(obj, *args)
    return obj

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
                                         if not (value is None or attr in attribs) }

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
    u = str(self.uri)
    suffix = '%s/%s' % (prefix, uuid.uuid1()) if prefix else str(uuid.uuid1())
    if   u.endswith(('/', '#')): return '%s%s'  % (u, suffix)
    elif sibling:
      slash = u.rfind('/')
      hash  = u.rfind('#')
      if hash > slash:           return '%s#%s' % (u.rsplit('#', 1)[0], suffix)
      else:                      return '%s/%s' % (u.rsplit('/', 1)[0], suffix)
    else:                        return '%s/%s' % (u, suffix)

  def save_to_graph(self, graph):
  #------------------------------
    '''
    Add RDF statements about ourselves to a graph.

    '''
    if (self.metaclass):
      graph.append(rdf.Statement(self.uri, rdf.RDF.type, self.metaclass))
      graph.add_statements(self.rdfmap.statement_stream(self))

  def metadata_as_graph(self):
  #---------------------------
    """
    Return metadata in a RDF graph.
    """
    graph = rdf.Graph(self.uri)
    self.save_to_graph(graph)
    return graph

  def metadata_as_string(self, format=rdf.Format.RDFXML, prefixes={ }):
  #--------------------------------------------------------------------
    """
    Return metadata as a serialised RDF string.
    """
    namespaces = { 'bsml': BSML.URI }
    namespaces.update(rdf.NAMESPACES)
    namespaces.update(prefixes)
    return self.metadata_as_graph().serialise(base=str(self.uri) + '/',
                                  format=format, prefixes=namespaces)

  def _assign(self, attr, value):
  #------------------------------
    if attr in self.__dict__: setattr(self, attr, value)
    else:                     self.metadata[attr] = value

  def load_from_graph(self, graph):
  #--------------------------------
    """
    Set attributes from RDF triples in a graph.

    :param graph: A graph of RDF statements.
    :type graph: :class:`biosignalml.rdf.Graph`
    """
    if graph.contains(rdf.Statement(self.uri, rdf.RDF.type, self.metaclass)):
      for stmt in graph.get_statements(rdf.Statement(self.uri, None, None)):
        s, attr, v = self.rdfmap.metadata(stmt, self.metaclass) # Need to go up __mro__ from AbstractObject
        ##logging.debug("%s: %s='%s'", self.uri, attr, v)  ###
        self._assign(attr, v)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of a resource, setting attributes from RDF triples in a graph.

    :param uri: The URI for the resource.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`AbstractObject`
    '''
    self = cls(uri, **kwds)
    self.load_from_graph(graph)
    self.graph = graph
    return self

  def set_from_graph(self, attr, graph):
  #-------------------------------------
    '''
    Set an attribute from RDF statement in the form `(uri, attr, value)`.
    '''
    v = self.rdfmap.get_value_from_graph(self.uri, attr, graph)
    if v: self._assign(attr, v)


