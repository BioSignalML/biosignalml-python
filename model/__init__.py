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

import biosignalml.rdf as rdf
from biosignalml.ontology import BSML

from core import AbstractObject


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
    from biosignalml.timeline import TimeLine   ## Otherwise circular import...
    AbstractObject.__init__(self, uri, metadata=metadata)
    self.timeline = TimeLine(str(uri) + '/timeline')
    self._signals = { }
    self._signal_uris = [ ]
    self._events = { }

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
    #logging.debug("Adding signal: %s", signal.uri)
    if str(signal.uri) in self._signal_uris:
      raise Exception, "Signal '%s' already in recording" % signal.uri
    if signal.recording and str(signal.recording) != str(self.uri):  ## Set from RDF mapping...
      raise Exception, "Adding to '%s', but signal '%s' is in '%s'" % (self.uri, signal.uri, signal.recording)
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


  @classmethod
  def create_from_string(cls, uri, string, format='turtle', rdfmap=None, **kwds):
  #------------------------------------------------------------------------------
    """
    Create a new instance of a resource, setting attributes from RDF statements in a string.

    :param uri: The URI for the resource.
    :param string: The RDF to parse and add.
    :type string: str
    :param format: The string's RDF format.
    :param rdfmap: How to map properties to attributes.
    :type rdfmap: :class:`~biosignalml.model.mapping.Mapping`
    :rtype: :class:`AbstractObject`
    """
    graph = Graph.create_from_string(string, format, uri)
    self = cls(uri, **kwds)
#    self = cls(uri, timeline=graph.get_object(uri, TL.timeline).uri, **kwds)
    self.load_from_graph(graph, rdfmap, **kwds)
    for s in graph.get_subjects(BSML.recording, self.uri):
      if graph.contains(Statement(s, RDF.type, BSML.Signal)):  ## UniformSignal ?? get rdf:type ??
        sig = AbstractSignal(s.uri)
        sig.load_from_graph(graph, rdfmap)
        self.add_signal(sig)
    return self




class AbstractEvent(AbstractObject):
#===================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event       #: :attr:`.BSML.Event`

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
