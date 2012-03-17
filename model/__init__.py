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
from biosignalml.ontology import BSML

from core import AbstractObject


class AbstractSignal(AbstractObject):
#====================================
  """
  An abstract BioSignalML Signal.

  :param uri: The URI of the signal.
  :param units: The physical units of the signal's data.
  """

  metaclass = BSML.Signal     #: :attr:`.BSML.Signal`

  attributes = ['label', 'units', 'transducer', 'filter', 'rate',  'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
                'index'
               ]
  '''Generic attributes of a Signal.'''

  def __init__(self, uri, units, metadata=None, **kwds):
  #-----------------------------------------------------
    kwds['units'] = units
    AbstractObject.__init__(self, uri, metadata=metadata, **kwds)
    self.recording = None


class AbstractRecording(AbstractObject):
#=======================================
  '''
  An abstract BioSignalML Recording.

  :param uri: The URI of the recording.
  '''

  metaclass = BSML.Recording  #: :attr:`.BSML.Recording`

  attributes = [ 'label', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration',
               ]
  '''Generic attributes of a Recording.'''

  SignalClass = AbstractSignal


  def __init__(self, uri, metadata=None, **kwds):
  #----------------------------------------------
    from biosignalml.timeline import TimeLine   ## Otherwise circular import...
    AbstractObject.__init__(self, uri, metadata=metadata, **kwds)
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

  def set_signal(self, signal):
  #----------------------------
    '''
    Assign a :class:`Signal` to a Recording.

    :param signal: The signal to add to the recording.
    :type signal: :class:`Signal`
    :return: The 0-origin index of the signal in the recording.
    '''
    sig_uri = str(signal.uri)
    try:
      index = self._signal_uris.index(sig_uri)
    except ValueError:
      raise Exception, "Signal '%s' not in recording" % signal.uri
    if signal.recording and str(signal.recording) != str(self.uri):  ## Set from RDF mapping...
      raise Exception, "Adding to '%s', but signal '%s' is in '%s'" % (self.uri, sig_uri, signal.recording)
    if self._signals.get(sig_uri, None):
      raise Exception, "Recording already has signal added"
    signal.recording = self
    self._signals[sig_uri] = signal
    return index

  def add_signal(self, signal):
  #----------------------------
    '''
    Add a :class:`Signal` to a Recording.

    :param signal: The signal to add to the recording.
    :type signal: :class:`Signal`
    :return: The 0-origin index of the signal in the recording.
    '''
    #logging.debug("Adding signal: %s", signal.uri)
    sig_uri = str(signal.uri)
    if sig_uri in self._signal_uris:
      raise Exception, "Signal '%s' already in recording" % signal.uri
    self._signal_uris.append(sig_uri)
    return self.set_signal(signal)          # 0-origin index of newly added signal uri

  def new_signal(self, uri, units, id=None, **kwds):
  #-------------------------------------------------
    '''
    Create a new Signal and add it to the Recording.

    :param uri: The URI for the signal.
    :param sigclass: The class of Signal to create.
    :return: A Signal of type `sigclass`.
    '''
    if uri is None and id is None:
      raise Exception, "Signal must have 'uri' or 'id' specified"
    if uri is None:
      uri = str(self.uri) + '/signal/%s' % str(id)
    if uri in self._signal_uris:
      raise Exception, "Signal '%s' already in recording" % uri
    sig = self.SignalClass(uri, units, **kwds)
    self.add_signal(sig)
    return sig

  def get_signal(self, uri=None, index=None):
  #-----------------------------------------
    '''
    Retrieve a :class:`Signal` from a Recording.

    :param uri: The URI of the signal to get.
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


  def metadata_as_graph(self, rdfmap=None):
  #----------------------------------------
    """
    Return a Recording's metadata in a RDF graph.
    """
    ## Associate mapping with recording ??
    graph = rdf.Graph(self.uri)
    self.save_to_graph(graph, rdfmap)
    self.timeline.save_to_graph(graph, rdfmap)
    for s in self.signals(): s.save_to_graph(graph, rdfmap)
    for e in self._events.itervalues(): e.save_to_graph(graph, rdfmap)
    return graph

  @classmethod
  def create_from_graph(cls, uri, graph, rdfmap=None, **kwds):
  #-----------------------------------------------------------
    '''
    Create a new instance of a Recording, setting attributes from RDF triples in a graph.

    :param uri: The URI for the Recording.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :param rdfmap: How to map properties to attributes.
    :type rdfmap: :class:`~biosignalml.model.mapping.Mapping`
    :rtype: :class:`Recording`
    '''
    self = cls(uri, **kwds)
#    self = cls(uri, timeline=graph.get_object(uri, TL.timeline).uri, **kwds)
    self.load_from_graph(graph, rdfmap)
    for s in graph.get_subjects(BSML.recording, self.uri):
      if graph.contains(rdf.Statement(s, rdf.RDF.type, BSML.Signal)):  ## UniformSignal ?? get rdf:type ??
        self.add_signal(AbstractSignal.create_from_graph(str(s.uri), graph, rdfmap))
      else:
        self._signal_uris.append(str(s.uri))
    self.graph = graph
    return self

  @classmethod
  def create_from_string(cls, uri, string, format=rdf.Format.TURTLE, rdfmap=None, **kwds):
  #---------------------------------------------------------------------------------------
    """
    Create a new Recording, setting attributes from RDF statements in a string.

    :param uri: The URI for the Recording.
    :param string: The RDF to parse and add.
    :type string: str
    :param format: The string's RDF format.
    :param rdfmap: How to map properties to attributes.
    :type rdfmap: :class:`~biosignalml.model.mapping.Mapping`
    :rtype: :class:`Recording`
    """
    return cls.create_from_graph(uri, rdf.Graph.create_from_string(string, format, uri),
                                                                           rdfmap=rdfmap, **kwds)


class AbstractEvent(AbstractObject):
#===================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event       #: :attr:`.BSML.Event`

  attributes = [ 'description', 'factor', 'time', ]
  '''Generic attributes of an Event.'''

  def __init__(self, uri, metadata=None, **kwds):
  #-----------------------------------------------
    ##logging.debug('Event: %s (%s)', uri, repr(uri))
    AbstractObject.__init__(self, uri, metadata=metadata, **kwds)

  def save_to_graph(self, graph, rdfmap):
  #--------------------------------------
    AbstractObject.save_to_graph(self, graph, rdfmap)
    AbstractObject.save_to_graph(self.time, graph, rdfmap)
