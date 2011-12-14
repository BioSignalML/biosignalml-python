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
from datetime import datetime, timedelta
from isodate  import isoduration

from rdfmodel import Graph, Node, Uri, Statement


BSML_MAP_URI = 'file://' + os.path.dirname(os.path.abspath(__file__)) + '/mapping.ttl'

_datatypes = { 'xsd:float':              float,  # Needs to be full uri...
##                                                 XSD.float.uri etc...
               'xsd:double':             float,
               'xsd:integer':            long,
               'xsd:long':               long,
               'xsd:int':                int,
               'xsd:short':              int,
               'xsd:byte':               int,
               'xsd:nonPostiveInteger':  long,
               'xsd:nonNegativeInteger': long,
               'xsd:positiveInteger':    long,
               'xsd:negativeInteger':    long,
               'xsd:unsignedLong':       long,
               'xsd:unsignedInt':        long,
               'xsd:unsignedShort':      int,
               'xsd:unsignedByte':       int,
             }


def get_uri(v):
#==============
  return v.uri if getattr(v, 'uri', None) else str(v)

def datetime_to_isoformat(dt):
#=============================
  return dt.isoformat()

def isoformat_to_datetime(v):
#============================
  try:
    return datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
  except ValueError:
    return datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
  except Exception, msg:
    logging.error("Cannot convert datetime '%s': %s", v, msg)
    return None  

def seconds_to_isoduration(secs):
#================================
  return isoduration.duration_isoformat(
    timedelta(seconds=int(secs), microseconds=int(1000000*(secs - int(secs)) ))
    )

def isoduration_to_seconds(d):
#=============================
  try:
    td = isoduration.parse_duration(d)
    return td.days*86400 + td.seconds + td.microseconds/1000000.0
  except:
    pass
  return 0


_modules = """
prefix dcterms: <http://purl.org/dc/terms/>
prefix map:     <http://www.biosignalml.org/ontologies/2011/02/mapping#>

select ?mod ?source
  where {
    ?m a map:MapModule .
    ?m map:prefix ?mod .
    ?m dcterms:source ?source .
    }
"""

_map_query = """
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix map:  <http://www.biosignalml.org/ontologies/2011/02/mapping#>

select ?lbl ?prop ?class ?otype ?map ?rmap
  where {
    ?m a map:Mapping .
    ?m rdfs:label ?lbl .
    ?m map:property ?prop .
    optional { ?m map:class ?class }
    optional { ?m map:object ?otype }
    optional { ?m map:mapped-by ?map }
    optional { ?m map:reverse-map ?rmap }
    }
"""

def _uri_protocol(u):
#====================
  return u.startswith('file:') or u.startswith('http:')


class MapEntry(object):
#======================

  def __init__(self, label, cls, prop, dtype, mapfn, rmapfn):
  #----------------------------------------------------------
    self.label = label
    self.cls = cls
    self.prop = prop
    self.dtype = dtype
    self.mapfn = mapfn
    self.rmapfn = rmapfn

class ReverseEntry(object):
#==========================

  def __init__(self, label, dtype, mapfn):
  #---------------------------------------
    self.label = label
    self.dtype = dtype
    self.mapfn = mapfn


def _load_mapping(mapfile):
#==========================
  mapping = { }
  maps = Graph()
  maps.parse(mapfile if _uri_protocol(mapfile) else 'file://' + os.path.abspath(mapfile), 'turtle')
  for s in maps.query(_modules):
    try:
      module = str(s['mod'])
      if globals().get(module) is None:
        fpath = os.path.split(os.path.abspath(mapfile))[0]
        fname = os.path.split(os.path.abspath(str(s['source'])))[1]
        globals()[module] = importlib.import_module(os.path.splitext(fname)[0], fpath)
    except Exception, msg:
      logging.error("Error loading mapping '%s':", str(s['source']), msg)
      pass
  for s in maps.query(_map_query):
    label = str(s['lbl'])
    cls = str(s['class'].uri) if s['class'] else None
    key = label + (cls if cls else '')
    mapping[key] = MapEntry(label, cls,
                     s['prop'].uri,
                     s['otype'].uri if s['otype'] else None,
                     str(s['map'])  if s['map']   else None,
                     str(s['rmap']) if s['rmap']  else None)
  return mapping

# Generic (BSML) mapping; format specific overrides.
_bsml_maps    = None
_bsml_mapping = None


def bsml_mapping():
#==================
  return _bsml_mapping


class Mapping(object):
#=====================

  def __init__(self, mapfile=None):
  #--------------------------------
    self._mapping = _bsml_maps.copy()
    if mapfile:
      if isinstance(mapfile, list):
        for mf in mapfile: self._mapping.update(_load_mapping(mf))
      else:
        self._mapping.update(_load_mapping(mapfile))
    self._reverse = { (str(m.prop) + (m.cls if m.cls else '')):
       ReverseEntry(m.label, m.dtype, m.rmapfn) for m in self._mapping.itervalues() }

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
        try: v = eval(mapfn)(v)
        except Exception, msg:
          logging.error("Exception mapping literal with '%s': %s", str(mapfn), msg)
      v = unicode(v)
      if _uri_protocol(v):
        return Node(Uri(v))
      else:
        result = { 'literal': v }
        if dtype: result['datatype'] = dtype
        return Node(**result)

  def statement(self, s, attr, v):
  #-------------------------------
    m = self._mapping[attr]
    return (s, m[0], self._makenode(v, m[1], m[2]))

  def statement_stream(self, metadata):
  #------------------------------------
    if getattr(metadata, 'uri', None):
      subject = metadata.uri
      metaclasses = [ str(cls.metaclass) for cls in metadata.__class__.__mro__
                      if cls.__dict__.get('metaclass') ]
      metadict = getattr(metadata, 'metadata', { })
      for attr, m in self._mapping.iteritems():
        if m.cls is None or m.cls in metaclasses:  ## Or do we need str() before lookup ??
          if getattr(metadata, m.label, None) not in [None, '']:
            yield Statement(subject, m.prop, self._makenode(getattr(metadata, m.label), m.dtype, m.mapfn))
          if metadict.get(m.label, None) not in [None, '']:
            yield Statement(subject, m.prop, self._makenode(metadict.get(m.label), m.dtype, m.mapfn))


  @staticmethod
  def _makevalue(node, dtype, rmapfn):
  #-----------------------------------
    if   not node: return None
    elif node.is_resource(): v = node.uri
    elif node.is_blank(): v = node.blank
    else:
      v = node.literal[0]
      if dtype: v = _datatypes.get(dtype, str)(v) 
    return eval(rmapfn)(v) if rmapfn else v

  def metadata(self, statement, cls):
  #----------------------------------
    m = self._reverse.get(str(statement.predicate.uri) + (str(cls) if cls else ''), None)
    if m is None: m = self._reverse.get(str(statement.predicate.uri), ReverseEntry(None, None, None))
    return (statement.subject.uri, m.label, self._makevalue(statement.object, m.dtype, m.mapfn))

  def get_value_from_graph(self, source, attr, graph):
  #---------------------------------------------------
    m = self._mapping[attr]
    return self._makevalue(graph.get_property(source, m.label), m.prop, m.dtype)


def initialise():
#================
  global _bsml_maps, _bsml_mapping
  if _bsml_maps is None:
    _bsml_maps = _load_mapping(BSML_MAP_URI)
    _bsml_mapping = Mapping()   # Standard model


initialise()


#def shutdown():
##==============
#  global _bsml_maps, _bsml_mapping
#  if _bsml_maps:
#    del _bsml_maps
#    _bsml_maps = None
#  if _bsml_mapping:
#    del _bsml_mapping
#    _bsml_mapping = None


if __name__ == '__main__':
#=========================

  class C(object):
    def __init__(self):
      self.uri = 'uri'
      self.version = 1
      self.metadata = { 'description': 'Hello...' }

  md = Graph()
  md.add_metadata(C(), Mapping())
  print md
