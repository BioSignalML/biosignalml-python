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
from collections import OrderedDict

import biosignalml.utils as utils
import biosignalml.rdf as rdf
from biosignalml.ontology import BSML
from biosignalml.rdf import XSD, RDF, DCTERMS, TL, OA, CNT

import mapping
from mapping import PropertyMap
import core

def makelabel(label, suffix):
#============================
  """
  Helper function to generate a meaningful label for sub-properties of resources.

  :param label: The label of some resource.
  :param suffix: A suffix to append to the label.
  :return: A string consisting of the label, a '_', and the suffix.
  """
  return label + '_' + suffix


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
                'index', 'signaltype', 'offset', 'duration',
               ]
  '''Generic attributes of a Signal.'''

  mapping = { ('recording',    metaclass): PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              ('units',        metaclass): PropertyMap(BSML.units, to_rdf=mapping.get_uri),
##            ('transducer',   metaclass): PropertyMap(BSML.transducer),
              ('filter',       metaclass): PropertyMap(BSML.preFilter),
              ('rate',         metaclass): PropertyMap(BSML.rate, XSD.double),
              ('clock',        metaclass): PropertyMap(BSML.clock, to_rdf=mapping.get_uri),
              ('minFrequency', metaclass): PropertyMap(BSML.minFrequency, XSD.double),
              ('maxFrequency', metaclass): PropertyMap(BSML.maxFrequency, XSD.double),
              ('minValue',     metaclass): PropertyMap(BSML.minValue, XSD.double),
              ('maxValue',     metaclass): PropertyMap(BSML.maxValue, XSD.double),
              ('index',        metaclass): PropertyMap(BSML.index, XSD.integer),
              ('signaltype',   metaclass): PropertyMap(BSML.signalType),
              ('offset',       metaclass): PropertyMap(BSML.offset, XSD.duration,
                                                       utils.seconds_to_isoduration,
                                                       utils.isoduration_to_seconds),
              ('duration',     metaclass): PropertyMap(DCTERMS.extent, XSD.duration,
                                                       utils.seconds_to_isoduration,
                                                       utils.isoduration_to_seconds),
            }


  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    kwds['units'] = units
    core.AbstractObject.__init__(self, uri, **kwds)
    self.recording = None


def _get_timeline(tl):      # Stops a circular import
#--------------------
  from biosignalml.timeline import RelativeTimeLine
  return RelativeTimeLine(tl)


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
              ('timeline',      metaclass): PropertyMap(TL.timeline,
                                                        to_rdf=mapping.get_uri,
                                                        from_rdf=_get_timeline) }

  SignalClass = Signal       #: The class of Signals in the Recording


  def __init__(self, uri, **kwds):
  #-------------------------------
    from biosignalml.timeline import RelativeTimeLine   ## Otherwise circular import...
    core.AbstractObject.__init__(self, uri, **kwds)
    self.timeline = RelativeTimeLine(str(uri) + '/timeline')
    self._signals = OrderedDict()
    self._events = OrderedDict()

  def signals(self):
  #-----------------
    """
    The recording's signals as a list.
    """
    return self._signals.values()

  def add_signal(self, signal):
  #----------------------------
    '''
    Add a :class:`Signal` to a Recording.

    :param signal: The signal to add to the recording.
    :type signal: :class:`Signal`
    :return: The 0-origin index of the signal in the recording.
    '''
    sig_uri = str(signal.uri)
    if sig_uri in self._signals:
      raise Exception, "Signal '%s' already in recording" % signal.uri
    if signal.recording and str(signal.recording) != str(self.uri):  ## Set from RDF mapping...
      raise Exception, "Adding to '%s', but signal '%s' is in '%s'" % (self.uri, sig_uri, signal.recording)
    signal.recording = self
    self._signals[sig_uri] = signal
    return list(self._signals).index(sig_uri)

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
    if str(uri) in self._signals:
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
    if uri is None: uri = list(self._signals)[index]
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
  #------------------------------
    """
    Add a Recording's metadata to a RDF graph.

    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    core.AbstractObject.save_to_graph(self, graph)
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
    self.graph = graph
    return self


class Annotation(core.AbstractObject):
#=====================================
  '''
  An abstract BioSignalML Annotation.
  '''
  metaclass = BSML.Annotation  #: :attr:`.BSML.Annotation`

  attributes = [ 'target', 'tags', 'body', 'annotated', 'annotator' ]

  mapping = { ('target',    None): PropertyMap(OA.hasTarget, to_rdf=mapping.get_uri),
              ('annotated', None): PropertyMap(OA.annotated, XSD.dateTime,
                                               utils.datetime_to_isoformat,
                                               utils.isoformat_to_datetime),
              ('annotator', None): PropertyMap(OA.annotator, to_rdf=mapping.get_uri),
              ('body',      None): PropertyMap(OA.hasBody, to_rdf=mapping.get_uri),
              ('tags',      None): PropertyMap(OA.hasSemanticTag),
            }

  class TextContent(core.AbstractObject):
  #======================================
    '''
    The text of an Annotation.
    '''

    metaclass = CNT.ContentAsText

    attributes = [ 'text', 'encoding' ]

    mapping = { ('text',     None): PropertyMap(CNT.chars),
                ('encoding', None): PropertyMap(CNT.characterEncoding) }

    def __init__(self, uri, text='', **kwds):
    #----------------------------------------
      if isinstance(text, unicode): utf8 = text.encode('utf-8')
      else:                         utf8 = unicode(text, 'utf-8')
      core.AbstractObject.__init__(self, uri, text=utf8, encoding='utf-8', **kwds)

  def __init__(self, uri, target=None, annotator=None, set_time=True, text=None, tags=None, body=None, **kwds):
  #------------------------------------------------------------------------------------------------------------
    annotated = kwds.pop('annotated', utils.utctime()) if set_time else None
    label = kwds.get('label', '')
    core.AbstractObject.__init__(self, uri, target=target,
      annotator=annotator, annotated=annotated, **kwds)
    self.body = Annotation.TextContent(rdf.Resource.uuid_urn(), text, label=makelabel(label, 'ann')) if text else body
    self.tags = tags if tags else []

  @classmethod
  def Note(cls, uri, target, annotator, text, **kwds):
  #---------------------------------------------------
    return cls(uri, target, annotator, text=text, **kwds)

  @classmethod
  def Tag(cls, uri, target, annotator, tag, **kwds):
  #-------------------------------------------------
    return cls(uri, target, annotator, tags=[tag], **kwds)

  def tag(self, tag):
  #------------------
    self.tags.append(tag)

  def save_to_graph(self, graph):
  #------------------------------
    """
    Add an Annotation's metadata to a RDF graph.

    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    core.AbstractObject.save_to_graph(self, graph)
    if self.body: self.body.save_to_graph(graph)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of an Annotation, setting attributes from RDF triples in a graph.

    :param uri: The URI of the Annotation.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`Annotation`
    '''
    self = cls(uri, set_time=False, **kwds)
    self.load_from_graph(graph)
    for b in graph.get_objects(self.uri, OA.hasBody):
      self.body = Annotation.TextContent.create_from_graph(b, graph)
      # Should only have the one body...
    return self

  '''
  @classmethod
  def Graph(cls, uri, target, graph, annotator):
    return cls(uri, target=target, type=AO.GraphAnnotation, body=graph, annotator=annotator)

  @classmethod
  def Qualifier(cls, uri, target, qualifier, annotator):
    return cls(uri, target=target, type=AO.Qualifier, body=qualifier, annotator=annotator)
  '''


class Event(Annotation):
#=======================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event              #: :attr:`.BSML.Event`

  class Selector(core.AbstractObject):
  #===================================
    """
    A temporal fragment given the event's position.
    """
    metaclass = OA.FragmentSelector
    attributes = [ 'time' ]
    mapping = { ('time', None): PropertyMap(RDF.value,
                                  to_rdf=lambda t: 't=%g,%g' % (t.start, t.end),
#                                 from_rdf=lambda s:
                                  ) }

    def __init__(self, uri, time=None, **kwds):
    #------------------------------------------
      core.AbstractObject.__init__(self, uri, time=time, **kwds)


  class Fragment(core.AbstractObject):
  #===================================
    """
    A temporal fragment giving the event's position.
    """
    metaclass = OA.SpecificResource
    attributes = [ 'source', 'selector' ]
    mapping = { ('source',   None): PropertyMap(OA.hasSource),
                ('selector', None): PropertyMap(OA.hasSelector) }

    def __init__(self, uri, source=None, time=None, **kwds):
    #-------------------------------------------------------
      label = kwds.get('label', '')
      core.AbstractObject.__init__(self, uri, source=source,
        selector=Event.Selector(rdf.Resource.uuid_urn(), time, label=makelabel(label, 'time'))
                 if time is not None else None,
        **kwds)

    def save_to_graph(self, graph):
    #------------------------------
      core.AbstractObject.save_to_graph(self, graph)
      self.selector.save_to_graph(graph)


  def __init__(self, uri, target=None, time=None, **kwds):
  #-------------------------------------------------------
    ##logging.debug('Event: %s (%s)', uri, repr(uri))
    label = kwds.get('label', '')
    Annotation.__init__(self, uri,
      target=Event.Fragment(rdf.Resource.uuid_urn(), target, time, label=makelabel(label, 'frag'))
             if target is not None else None, **kwds)

  @property
  def time(self):
  #--------------
    return self.target.selector.time

  def save_to_graph(self, graph):
  #------------------------------
    """
    Add an Event's metadata to a RDF graph.

    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    Annotation.save_to_graph(self, graph)
    self.target.save_to_graph(graph)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of an Event, setting attributes from RDF triples in a graph.

    :param uri: The URI of the Event.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`Event`
    '''
    self = super(Event, cls).create_from_graph(uri, graph, **kwds)
    self.load_from_graph(graph)
    for t in graph.get_objects(self.uri, OA.hasTarget):
      self.target = Event.Fragment.create_from_graph(t, graph)
      for s in graph.get_objects(self.target.uri, OA.hasSelector):
        self.target.selector = Event.Selector.create_from_graph(s, graph)
        print self.target.selector
      ################ Need to set selector's time...
    return self
