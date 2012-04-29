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

import logging
from datetime import datetime

import biosignalml.utils as utils
import biosignalml.rdf as rdf
from biosignalml.ontology import BSML
from biosignalml.rdf import XSD, DCTERMS, TL, OA, CNT, EVT

import mapping
from mapping import PropertyMap
import core


class Signal(core.AbstractObject):
#=================================
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

  mapping = { ('recording',    metaclass): PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              ('units',        metaclass): PropertyMap(BSML.units, to_rdf=mapping.get_uri),
##            ('transducer',   metaclass): PropertyMap(BSML.transducer),
              ('filter',       metaclass): PropertyMap(BSML.preFilter),
              ('rate',         metaclass): PropertyMap(BSML.rate, XSD.double),
##            ('clock',        metaclass): PropertyMap(BSML.sampleClock, to_rdf=mapping.get_uri),
              ('minFrequency', metaclass): PropertyMap(BSML.minFrequency, XSD.double),
              ('maxFrequency', metaclass): PropertyMap(BSML.maxFrequency, XSD.double),
              ('minValue',     metaclass): PropertyMap(BSML.minValue, XSD.double),
              ('maxValue',     metaclass): PropertyMap(BSML.maxValue, XSD.double),
              ('index',        metaclass): PropertyMap(BSML.index, XSD.integer) }


  def __init__(self, uri, units, metadata=None, **kwds):
  #-----------------------------------------------------
    kwds['units'] = units
    core.AbstractObject.__init__(self, uri, metadata=metadata, **kwds)
    self.recording = None


def _get_timeline(tl):      # Stops a circular import
#--------------------
  from biosignalml.timeline import TimeLine
  return TimeLine(tl)

class Recording(core.AbstractObject):
#====================================
  '''
  An abstract BioSignalML Recording.

  :param uri: The URI of the recording.
  '''

  metaclass = BSML.Recording  #: :attr:`.BSML.Recording`

  attributes = [ 'label', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration', 'timeline'
               ]
  '''Generic attributes of a Recording.'''

  mapping = { ('format',        metaclass): PropertyMap(DCTERMS.format),
              ('source',        metaclass): PropertyMap(DCTERMS.source),
              ('investigation', metaclass): PropertyMap(DCTERMS.subject),
              ('starttime',     metaclass): PropertyMap(DCTERMS.created, XSD.dateTime,
                                                        utils.datetime_to_isoformat,
                                                        utils.isoformat_to_datetime),
              ('duration',      metaclass): PropertyMap(DCTERMS.extent, XSD.duration,
                                                        utils.seconds_to_isoduration,
                                                        utils.isoduration_to_seconds),
##            ('digest',        metaclass): PropertyMap(BSML.digest),
              ('timeline', metaclass):      PropertyMap(TL.timeline,
                                                        to_rdf=mapping.get_uri,
                                                        from_rdf=_get_timeline) }

  SignalClass = Signal       #: The class of Signals in the Recording


  def __init__(self, uri, metadata=None, **kwds):
  #----------------------------------------------
    from biosignalml.timeline import TimeLine   ## Otherwise circular import...
    core.AbstractObject.__init__(self, uri, metadata=metadata, **kwds)
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


  def save_to_graph(self, graph):
  #---------------------------
    """
    Add a Recording's metadata to a RDF graph.

    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    core.AbstractObject.save_to_graph(self, graph)
    self.timeline.save_to_graph(graph)
    for s in self.signals(): s.save_to_graph(graph)
    for e in self._events.itervalues(): e.save_to_graph(graph)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of a Recording, setting attributes from RDF triples in a graph.

    :param uri: The URI for the Recording.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`Recording`
    '''
    self = cls(uri, **kwds)
#    self = cls(uri, timeline=graph.get_object(uri, TL.timeline).uri, **kwds)
    self.load_from_graph(graph)
    for s in graph.get_subjects(BSML.recording, self.uri):
      if graph.contains(rdf.Statement(s, rdf.RDF.type, BSML.Signal)):  ## UniformSignal ?? get rdf:type ??
        self.add_signal(self.SignalClass.create_from_graph(str(s.uri), graph, units=None))
      else:
        self._signal_uris.append(str(s.uri))
    self.graph = graph
    return self


class Event(core.AbstractObject):
#================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event              #: :attr:`.BSML.Event`

  attributes = [ 'factor', 'time', ]   #: '''Generic attributes of an Event.'''

  mapping = { ('time',   metaclass): PropertyMap(TL.time),
              ('factor', metaclass): PropertyMap(EVT.factor) }

  def __init__(self, uri, metadata=None, **kwds):
  #-----------------------------------------------
    ##logging.debug('Event: %s (%s)', uri, repr(uri))
    core.AbstractObject.__init__(self, uri, metadata=metadata, **kwds)

  def save_to_graph(self, graph):
  #------------------------------
    core.AbstractObject.save_to_graph(self, graph)
    core.AbstractObject.save_to_graph(self.time, graph)


class Annotation(core.AbstractObject):
#=====================================
  '''
  An abstract BioSignalML Annotation.
  '''

  metaclass = BSML.Annotation  #: :attr:`.BSML.Annotation`

  attributes = [ 'target', 'body', 'created', 'creator' ]

  def __init__(self, uri, metadata=None, **kwds):
    core.AbstractObject.__init__(self, uri, metadata=metadata, created=datetime.utcnow(), **kwds)

  @classmethod
  def Note(cls, uri, target, text, creator):
    return cls(uri, target=target, body=unicode(text), creator=creator)  # A0.Note

  '''
  @classmethod
  def Tag(cls, uri, target, label, annotator):
    return cls(uri, target=target, type=AO.Tag, body=unicode(label), annotator=annotator)

  @classmethod
  def Graph(cls, uri, target, graph, annotator):
    return cls(uri, target=target, type=AO.GraphAnnotation, body=graph, annotator=annotator)

  @classmethod
  def Qualifier(cls, uri, target, qualifier, annotator):
    return cls(uri, target=target, type=AO.Qualifier, body=qualifier, annotator=annotator)
  '''
