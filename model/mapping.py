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
import importlib  # Python 2.7 onwards...
from collections import namedtuple

from biosignalml.ontology import BSML
from biosignalml.rdf import Node, Uri, Statement
from biosignalml.rdf import RDF, RDFS, DCTERMS, XSD, TL, EVT, AO, PAV
from biosignalml.utils import datetime_to_isoformat, isoformat_to_datetime
from biosignalml.utils import seconds_to_isoduration, isoduration_to_seconds

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

def make_timeline(uri):
#======================
  import biosignalml.timeline as timeline
  return timeline.TimeLine(uri)

class PropertyMap(object):
#=========================

  def __init__(self, property, datatype=None, to_rdf=None, from_rdf=None):
  #-----------------------------------------------------------------------
    self.property = property
    self.datatype = datatype
    self.to_rdf = to_rdf
    self.from_rdf = from_rdf


DEFAULT_MAP = {
# Generic metadata:
              ('label',           None): PropertyMap(RDFS.label),
              ('comment',         None): PropertyMap(RDFS.comment),
              ('description',     None): PropertyMap(DCTERMS.description),
              ('dateSubmitted" ', None): PropertyMap(DCTERMS.dateSubmitted),

# Recording specific metadata:
              ('format',        BSML.Recording): PropertyMap(DCTERMS.format),
              ('source',        BSML.Recording): PropertyMap(DCTERMS.source),
              ('investigation', BSML.Recording): PropertyMap(DCTERMS.subject),
              ('starttime',     BSML.Recording): PropertyMap(DCTERMS.created,
                                                   XSD.dateTime, datetime_to_isoformat,
                                                                 isoformat_to_datetime),
              ('duration',      BSML.Recording): PropertyMap(DCTERMS.extent,
                                                   XSD.duration, seconds_to_isoduration,
                                                                 isoduration_to_seconds),
##            ('digest',        BSML.Recording): PropertyMap(BSML.digest),

# Timing specific metadata:
              ('timeline', None):                PropertyMap(TL.timeline,
                                                   to_rdf=get_uri, from_rdf=make_timeline),
              ('at',       TL.RelativeInstant):  PropertyMap(TL.atDuration,
                                                   XSD.duration, seconds_to_isoduration,
                                                                 isoduration_to_seconds),
              ('start',    TL.RelativeInterval): PropertyMap(TL.beginsAtDuration,
                                                   XSD.duration, seconds_to_isoduration,
                                                                 isoduration_to_seconds),
              ('duration', TL.RelativeInterval): PropertyMap(TL.durationXSD,
                                                   XSD.duration, seconds_to_isoduration,
                                                                 isoduration_to_seconds),

# Event specific metadata:
              ('time',   BSML.Event): PropertyMap(TL.time),
##            ('factor', BSML.Event): PropertyMap(EVT.factor),   ????????????

# Signal specific metadata:
              ('recording',    BSML.Signal): PropertyMap(BSML.recording, to_rdf=get_uri),
              ('units',        BSML.Signal): PropertyMap(BSML.units, to_rdf=get_uri),
##            ('transducer',   BSML.Signal): PropertyMap(BSML.transducer),
              ('filter',       BSML.Signal): PropertyMap(BSML.preFilter),
              ('rate',         BSML.Signal): PropertyMap(BSML.rate, XSD.double),
##            ('clock',        BSML.Signal): PropertyMap(BSML.sampleClock, to_rdf=get_uri),
              ('minFrequency', BSML.Signal): PropertyMap(BSML.minFrequency, XSD.double),
              ('maxFrequency', BSML.Signal): PropertyMap(BSML.maxFrequency, XSD.double),
              ('minValue',     BSML.Signal): PropertyMap(BSML.minValue, XSD.double),
              ('maxValue',     BSML.Signal): PropertyMap(BSML.maxValue, XSD.double),
              ('index',        BSML.Signal): PropertyMap(BSML.index, XSD.integer),

# Annotation specific metadata:
              ('type',        BSML.Annotation): PropertyMap(RDF.type, to_rdf=get_uri),
              ('target',      BSML.Annotation): PropertyMap(AO.annotatesResource, to_rdf=get_uri),
              ('body',        BSML.Annotation): PropertyMap(AO.body),
              ('created',     BSML.Annotation): PropertyMap(PAV.createdOn,
                                                  XSD.dateTime, datetime_to_isoformat,
                                                                isoformat_to_datetime),
              ('creator',     BSML.Annotation): PropertyMap(PAV.createdBy, to_rdf=get_uri),
            }


ReverseEntry = namedtuple('ReverseEntry', 'attribute, datatype, from_rdf')
#===========

class Mapping(object):
#=====================

  def __init__(self, usermap=None):
  #--------------------------------
    if usermap:
      self.mapping = DEFAULT_MAP.copy()
      self.mapping.update(usermap)
    else:
      self.mapping = DEFAULT_MAP
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
          if getattr(resource, k[0], None) not in [None, '']:
            yield Statement(subject, m.property, self._makenode(getattr(resource, k[0]), m.datatype, m.to_rdf))
          if metadict.get(k[0], None) not in [None, '']:
            yield Statement(subject, m.property, self._makenode(metadict.get(k[0]), m.datatype, m.to_rdf))


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

  class MyRecording(Recording):
  #----------------------------
    rdfmap = Mapping( { ('xx', None): PropertyMap(DCTERMS.subject) } )


  r = MyRecording('http://example.org/uri1', description='Hello', xx = 'subject')
  g = rdf.Graph()
  r.save_to_graph(g)


  s = MyRecording.create_from_graph('http://example.org/uri1', g, comment='From graph')
  print s.metadata_as_string(rdf.Format.TURTLE)
