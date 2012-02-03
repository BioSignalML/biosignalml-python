'''
Abstract BioSignalML objects.
'''
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


import uuid
import logging

from biosignalml.rdf import NAMESPACES, RDF, EVT
from biosignalml.rdf import Uri, Statement, Graph

from ontology import BSML
from mapping import bsml_mapping


class AbstractObject(object):
#============================
  '''
  A general abstract resource with metadata.

  :param uri: URI of the resource,
  :type uri: str
  :param metadata: Dictionary containing metadata values for the resource.
  :type metadata: dict

  Resource properties with names in the :attr:`attributes` list are stored as attributes
  of the class instance; other elements are stored in the :attr:`metadata` dictionary.
  '''

  metaclass = None
  '''Class in BioSignalML Ontology as a :class:`biosignalml.rdf.Resource`'''

  attributes = [ 'uri', 'description' ]
  '''List of generic attributes all resources have.'''

  def __init__(self, uri, metadata={}):
  #------------------------------------
    self.metadata = { }
    '''Dictionary of property values with names not in :attr:`attributes` list.'''
    self.set_attributes(metadata)
    self.uri = Uri(uri)

  def __str__(self):
  #-----------------
    return '[%s: %s]' % (self.__class__, self.uri)

  def set_attributes(self, values):
  #--------------------------------
    '''
    Set attribute if `key` exists in an :attr:`attributes` list of any class in hierarchy.

    :param meta: Dictionary of `{ key: value }` pairs to set as attributes.
    :type meta: dict
    '''
    assigned = [ ]
    for cls in self.__class__.__mro__:
      if 'attributes' in cls.__dict__:
        for attr in cls.__dict__['attributes']:
          setattr(self, attr, values.get(attr, None))
          assigned.append(attr)
    for attr, value in values.iteritems():
      if attr not in assigned: self.metadata[attr] = value

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

  def make_uri(self, sibling=False):
  #---------------------------------
    '''
    Generate a unique URI that starts with the resource's URI.

    :param sibling: When set, replace the last component of our URI with unique text.
      The default is to append unique text to our URI.
    :type: bool
    :return: A unique URI.
    :rtype: str
    '''
    u = str(self.uri)
    if   u.endswith(('/', '#')): return '%s%s'  % (u, uuid.uuid1())
    elif sibling:
      slash = u.rfind('/')
      hash  = u.rfind('#')
      if hash > slash:           return '%s#%s' % (u.rsplit('#', 1)[0], uuid.uuid1())
      else:                      return '%s/%s' % (u.rsplit('/', 1)[0], uuid.uuid1())
    else:                        return '%s/%s' % (u, uuid.uuid1())

  def save_to_graph(self, graph, rdfmap=None):
  #-------------------------------------------
    '''
    Add RDF statements about ourselves to a graph.

    '''
    if rdfmap is None: rdfmap = bsml_mapping()
    if (self.metaclass):
      graph.append(Statement(self.uri, RDF.type, self.metaclass))
      graph.add_statements(rdfmap.statement_stream(self))

  def _assign(self, attr, value):
  #------------------------------
    if attr in self.__dict__: setattr(self, attr, value)
    else:                     self.metadata[attr] = value

  @classmethod
  def create_from_store(cls, uri, store, rdfmap=None, **kwds):
  #-----------------------------------------------------------
    '''
    Create a new instance of a resource, setting attributes from RDF triples in a triple store.

    :param uri: The URI for the resource.
    :param store: A RDF triple store.
    :type store: :class:`biosignalml.repostory.Repository`
    :param rdfmap: How to map properties to attributes.
    :type rdfmap: :class:`biosignalml.model.Mapping`
    :rtype: :class:`AbstractObject`
    '''
    if rdfmap is None: rdfmap = bsml_mapping()
    self = cls(uri, **kwds)
    statements = store.statements('<%(uri)s> ?p ?o',
                                  '<%(uri)s> a  <%(type)s> . <%(uri)s> ?p ?o',
                                  { 'uri': str(uri), 'type': str(self.metaclass) })
    for stmt in statements:
      s, attr, v = rdfmap.metadata(stmt, self.metaclass)
      ##logging.debug("%s='%s'", attr, v)
      self._assign(attr, v)
    return self

  def set_from_graph(self, attr, graph, rdfmap=None):
  #--------------------------------------------------
    '''
    Set an attribute from RDF statement in the form `(uri, attr, value)`.


    '''
    if rdfmap is None: rdfmap = bsml_mapping()
    v = rdfmap.get_value_from_graph(self.uri, attr, graph)
    if v: self._assign(attr, v)


class AbstractRecording(AbstractObject):
#======================================
  '''
  An abstract BioSignalML Recording.
  '''

  metaclass = BSML.Recording  #: :attr:`.BSML.Recording`

  attributes = [ 'label', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration',
               ]
  '''Generic attributes of a Recording.'''

  def __init__(self, uri, metadata={}):
  #------------------------------------
    AbstractObject.__init__(self, uri, metadata=metadata)
    self.timeline = TimeLine(str(uri) + '/timeline')  ## Only if Recording doesn't have one ??
    self._signals = { }
    self._signal_uris = [ ]
    self._events = { }

  def load_signals_from_store(self, store, rdfmap=None):
  #-----------------------------------------------------
    """
    Retrieve the recording's signals from a triple store.

    :param store: A RDF triple store.
    :type store: :class:`biosignalml.repostory.Repository`
    :param rdfmap: How to map properties to attributes.
    :type rdfmap: :class:`biosignalml.model.Mapping`
    """
    for sig in store.get_subjects(BSML.recording, self.uri):
      self.add_signal(AbstractSignal.create_from_store(sig, store, rdfmap))

  def signals(self):
  #-----------------
    """
    The recording's signals as a list.
    """
    return [ self._signals[s] for s in sorted(self._signal_uris) ]

  def add_signal(self, signal):
  #----------------------------
    '''
    Add a :class:`Signal` to a Recording.

    :param signal: The signal to add to the recording.
    :type signal: :class:`Signal`
    :return: The 0-origin index of the signal in the recording.
    '''
    logging.debug("Adding signal: %s", signal.uri)
    if signal.uri in self._signal_uris:
      raise Exception, "Signal '%s' already in recording" % signal.uri
    if signal.recording and str(signal.recording) != str(self.uri):  ## Set from RDF mapping...
      raise Exception, "Signal '%s' is in Recording '%s'" % (signal.uri, signal.recording)
    signal.recording = self
    self._signal_uris.append(str(signal.uri))
    self._signals[str(signal.uri)] = signal
    return len(self._signal_uris) - 1         # 0-origin index of newly added signal uri

  def get_signal(self, uri=None, index=None):
  #-----------------------------------------
    '''
    Retrieve a :class:`Signal` from a Recording.

    :param uri: The uri of the signal to get.
    :param index: The 0-origin index of the signal to get.
    :type index: int
    :return: A signal in the recording.
    :rtype: :class:`Signal`
    '''
    if uri is None: uri = self._signal_uris[index]
    return self._signals[str(uri)]

  def __len__(self):
  #-----------------
    return len(self._signals)


  def events(self):
  #-----------------
    return self._events.itervalues()

  def add_event(self, event):
  #--------------------------
    self._events[event.uri] = event
    event.factor = self

  def get_event(self, uri):
  #------------------------
    return self._events[uri]

  def instant(self, when):
  #----------------------
    """
    Create an :class:`.Instant` on the recording's timeline.
    """
    return self.timeline.instant(when)

  def interval(self, start, duration):
  #-----------------------------------
    """
    Create an :class:`.Interval` on the recording's timeline.
    """
    return self.timeline.interval(start, duration)


  def save_to_graph(self, rdfmap=None):
  #------------------------------------
    graph = Graph(self.uri)
    AbstractObject.save_to_graph(self, graph, rdfmap)
    AbstractObject.save_to_graph(self.timeline, graph, rdfmap)
    for s in self.signals(): s.save_to_graph(graph, rdfmap)
    for e in self._events.itervalues(): e.save_to_graph(graph, rdfmap)
    return graph


  def metadata_as_string(self, format='turtle', prefixes={ }, rdfmap=None):
  #------------------------------------------------------------------------
    namespaces = { 'bsml': BSML.uri }
    namespaces.update(NAMESPACES)
    namespaces.update(prefixes)
    return self.save_to_graph(rdfmap=rdfmap).serialise(base=str(self.uri) + '/', format=format, prefixes=namespaces)


class AbstractSignal(AbstractObject):
#====================================
  '''
  An abstract BioSignalML Signal.
  '''

  metaclass = BSML.Signal     #: :attr:`.BSML.Signal`

  attributes = ['label', 'units', 'transducer', 'filter', 'rate',  'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
               ]
  '''Generic attributes of a Signal.'''

  def __init__(self, uri, metadata={}):
  #------------------------------------
    AbstractObject.__init__(self, uri, metadata=metadata)
    self.recording = None


class AbstractEvent(AbstractObject):
#===================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = EVT.Event       #: :attr:`.BSML.Event`

  attributes = [ 'description', 'factor', 'time', ]
  '''Generic attributes of an Event.'''

  def __init__(self, uri, metadata={}):
  #------------------------------------
    ##logging.debug('Event: %s (%s)', uri, repr(uri))
    AbstractObject.__init__(self, uri, metadata=metadata)

  def save_to_graph(self, graph, rdfmap):
  #--------------------------------------
    AbstractObject.save_to_graph(self, graph, rdfmap)
    AbstractObject.save_to_graph(self.time, graph, rdfmap)
