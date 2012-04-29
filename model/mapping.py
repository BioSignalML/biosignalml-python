######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: bbd3c04 on Wed Jun 8 16:47:09 2011 +1200 by Dave Brooks $
#
######################################################


import os
import logging
from collections import namedtuple

from biosignalml.rdf import Node, Uri, Statement, XSD

URI_SCHEMES = [ 'http', 'file' ]

datatypes = { XSD.float:              float,
              XSD.double:             float,
              XSD.integer:            long,
              XSD.long:               long,
              XSD.int:                int,
              XSD.short:              int,
              XSD.byte:               int,
              XSD.nonPostiveInteger:  long,
              XSD.nonNegativeInteger: long,
              XSD.positiveInteger:    long,
              XSD.negativeInteger:    long,
              XSD.unsignedLong:       long,
              XSD.unsignedInt:        long,
              XSD.unsignedShort:      int,
              XSD.unsignedByte:       int,
            }


def get_uri(v):
#==============
  '''
  Get the `uri` attribute if it exists, otherwise the object as a string.
  '''
  return v.uri if getattr(v, 'uri', None) else str(v)


class PropertyMap(object):
#=========================

  def __init__(self, property, datatype=None, to_rdf=None, from_rdf=None):
  #-----------------------------------------------------------------------
    self.property = property
    self.datatype = datatype
    self.to_rdf = to_rdf
    self.from_rdf = from_rdf



ReverseEntry = namedtuple('ReverseEntry', 'attribute, datatype, from_rdf')
#===========

class Mapping(object):
#=====================

  def __init__(self, usermap=None):
  #--------------------------------
    self.mapping = { }
    self.reversemap = { }
    if usermap: self.update(usermap)

  def update(self, usermap):
  #-------------------------
    self.mapping.update(usermap)
    self.reversemap = { (str(m.property), k[1]): ReverseEntry(k[0], m.datatype, m.from_rdf)
                          for k, m in self.mapping.iteritems() }

  @staticmethod
  def _makenode(v, dtype, mapfn):
  #------------------------------
    if   isinstance(v, Node) or isinstance(v, Uri):
      return Node(v)
    elif getattr(v, 'uri', None):
      if isinstance(v.uri, Node): return Node(v)
      else:                       return Node(Uri(v.uri))
    else:
      if mapfn:
        try: v = mapfn(v)
        except Exception, msg:
          logging.error("Exception mapping literal with '%s': %s", str(mapfn), msg)
      v = unicode(v)
      if len(v.split(':')) > 1 and v.split(':')[0] in URI_SCHEMES:
        return Node(Uri(v))
      else:
        result = { 'literal': v }
        if dtype: result['datatype'] = dtype.uri
        return Node(**result)

  def _statements(self, subject, map, value):
  #----------------------------------------------
    if value not in [None, '']:
      if hasattr(value, '__iter__'):
        for v in value: yield Statement(subject, map.property,
                                        self._makenode(v, map.datatype, map.to_rdf))
      else:
        yield Statement(subject, map.property,
                        self._makenode(value, map.datatype, map.to_rdf))

  def statement_stream(self, resource):
  #------------------------------------
    """
    Generate :class:`Statement`\s from a resource's attributes and
    elements in its `metadata` dictionary.

    :param resource: An object with a `metaclass` attributes on
      some of its classes.

    All attributes defined in the mapping table are tested to see if they are defined for
    the resource, and if so, their value in the resource is translated to an object node
    in a RDF statement.
    """
    if getattr(resource, 'uri', None):
      subject = resource.uri
      metaclasses = [ c.metaclass for c in resource.__class__.__mro__ if c.__dict__.get('metaclass') ]
      metadict = getattr(resource, 'metadata', { })
      for k, m in self.mapping.iteritems():
        if k[1] is None or k[1] in metaclasses:  ## Or do we need str() before lookup ??
          for s in self._statements(subject, m, getattr(resource, k[0], None)): yield s
          for s in self._statements(subject, m, metadict.get(k[0], None)): yield s

  @staticmethod
  def _makevalue(node, dtype, from_rdf):
  #-------------------------------------
    if node is None: return None
    elif node.is_resource(): v = node.uri
    elif node.is_blank(): v = node.blank
    else:
      v = node.literal[0]
      if dtype: v = datatypes.get(dtype, str)(v) 
    return from_rdf(v) if from_rdf else v

  def metadata(self, statement, metaclass):
  #----------------------------------------
    """
    Given a RDF statement and a metaclass, lookup the statement's predicate
    in the reverse mapping table use its properties to translate the value of the
    statement's object.
    """
    m = self.reversemap.get((str(statement.predicate.uri), metaclass), None)
    if m is None: m = self.reversemap.get((str(statement.predicate.uri), None), ReverseEntry(None, None, None))
    return (statement.subject.uri, m.attribute, self._makevalue(statement.object, m.datatype, m.from_rdf))

  def get_value_from_graph(self, resource, attr, graph):
  #-----------------------------------------------------
    """
    Find the property corresponding to a resource's attribute and if a statement
    about the resource using the property is in the graph, translate and return
    its object's value.
    """
    m = self.mapping.get((attr, resource.metaclass), None)
    if m is None: m = self.mapping.get((attr, None))
    if m:
      return self._makevalue(graph.get_object(resource.uri, m.property), m.datatype, m.from_rdf)


if __name__ == '__main__':
#=========================

  from biosignalml import Recording
  import biosignalml.rdf as rdf

  #logging.basicConfig(level=logging.DEBUG)

  class MyRecording(Recording):
  #----------------------------
    mapping = { ('xx', None): PropertyMap(rdf.DCTERMS.subject),
                ('yy', None): PropertyMap('http://example.org/onto#subject'),
     }


  r = MyRecording('http://example.org/uri1', description='Hello', yy = ['subject', 'in', 'list'] )
  print r.metadata_as_string(rdf.Format.TURTLE)
  g = rdf.Graph()
  r.save_to_graph(g)


  s = MyRecording.create_from_graph('http://example.org/uri1', g, comment='From graph')
  print s.metadata_as_string(rdf.Format.TURTLE)
