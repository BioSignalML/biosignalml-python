######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2013  David Brooks
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
"""
An abstract BioSignalML Recording.
"""

import logging
from collections import OrderedDict

import biosignalml.rdf as rdf
import biosignalml.utils as utils
from biosignalml.rdf import XSD, DCT, TL, PROV

from .ontology import BSML
from .core     import AbstractObject
from .mapping  import PropertyMap
from .signal   import Signal
from .event    import Event
from .segment  import Segment

__all__ = [ 'Recording' ]


def _get_timeline(tl):      # Stops a circular import
#--------------------
  from biosignalml.data.time import RelativeTimeLine
  return RelativeTimeLine(tl)


class Recording(AbstractObject):
#===============================
  """
  An abstract BioSignalML Recording.

  :param uri: The URI of the recording.
  :param kwds: Recording attributes, specified as keywords.
  """

  metaclass = BSML.Recording  #: :attr:`.BSML.Recording`

  attributes = [ 'dataset', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration', 'timeline', 'generatedBy'
               ]              #: Generic attributes of a Recording.

  mapping = { 'format':        PropertyMap(DCT.format),
              'dataset':       PropertyMap(BSML.dataset),
              'source':        PropertyMap(DCT.source, functional=False),
              'investigation': PropertyMap(DCT.subject),
              'investigator':  PropertyMap(DCT.creator),
              'starttime':     PropertyMap(DCT.created, XSD.dateTime,
                                           utils.datetime_to_isoformat,
                                           utils.isoformat_to_datetime),
              'duration':      PropertyMap(DCT.extent, XSD.dayTimeDuration,
                                           utils.seconds_to_isoduration,
                                           utils.isoduration_to_seconds),
##            'digest':        PropertyMap(BSML.digest),
              'timeline':      PropertyMap(TL.timeline,
                                           to_rdf=PropertyMap.get_uri,
                                           from_rdf=_get_timeline, subelement=True),
              'generatedBy':   PropertyMap(PROV.wasGeneratedBy, to_rdf=PropertyMap.get_uri,
                                           subelement=True),
            }

  SignalClass = Signal       #: The class of :class:`~.signal.Signal`\s in the Recording
  EventClass  = Event        #: The class of :class:`~.event.Event`\s in the Recording


  def __init__(self, uri, **kwds):
  #-------------------------------
    from biosignalml.data.time import RelativeTimeLine   ## Otherwise circular import...
    AbstractObject.__init__(self, uri, **kwds)
    self.timeline = RelativeTimeLine(str(uri) + '/timeline')
    self._resources = OrderedDict()

  def add_resource(self, resource):
  #--------------------------------
    """Associate a resource with a Recording."""
    self._resources[str(resource.uri)] = resource
    return resource

  ## pop_resource(self, uri)      ???

  ## del_resource(self, uri)      ???

  def resources(self, cls):
  #-------------------------
    """
    The recording's resources of a given class, as a list.
    """
    return [ r for r in self._resources.values() if isinstance(r, cls) ]

  def get_resource(self, uri):
  #---------------------------
    """
    Get a resource associated with the Recording.

    :param uri: The resource's URI.

    """
    return self._resources.get(str(uri))

  def __len__(self):
  #-----------------
    return len(self.signals())

  def signals(self):
  #-----------------
    """
    The recording's signals as a list.
    """
    return self.resources(Signal)

  def get_signal(self, uri):
  #-------------------------
    """
    Retrieve a :class:`~.signal.Signal` from a Recording.

    :param uri: The URI of the signal.
    :return: A signal in the recording.

    """
    signal = self.get_resource(uri)
    if not isinstance(signal, self.SignalClass):
      raise KeyError, str(uri)
    return signal

  def add_signal(self, signal):
  #----------------------------
    """
    Add a :class:`~.signal.Signal` to a Recording.

    :param signal: The signal to add to the recording.

    """
    sig_uri = str(signal.uri)
    try:
      self.get_signal(sig_uri)
      raise Exception, "Signal '%s' already in recording" % sig_uri
    except KeyError:
      pass
    if signal.recording is not None:     ## Set from RDF mapping...
      if isinstance(signal.recording, Recording): rec_uri = signal.recording.uri
      else:                                       rec_uri = signal.recording
      if str(rec_uri) != str(self.uri):
        raise Exception, "Adding to '%s', but signal '%s' is in '%s'" % (self.uri, sig_uri, rec_uri)
    signal.recording = self
    self.add_resource(signal)
    return signal

  def new_signal(self, uri, units, id=None, **kwds):
  #-------------------------------------------------
    """
    Create a new Signal and add it to the Recording.

    :param uri: The URI for the signal.
    :param units: The units signal data values are in.
    :return: A Signal of type :attr:`SignalClass`.
    """
    if uri is None and id is None:
      raise Exception, "Signal must have 'uri' or 'id' specified"
    if uri is None:
      uri = str(self.uri) + '/signal/%s' % str(id)
    try:
      self.get_signal(uri)
      raise Exception, "Signal '%s' already in recording" % uri
    except KeyError:
      pass
    signal = self.SignalClass(uri, units, **kwds)
    signal.recording = self
    self.add_resource(signal)
    return signal


  def events(self):
  #-----------------
    """
    The recording's events as a list.
    """
    return self.resources(Event)

  def get_event(self, uri):
  #------------------------
    """
    Retrieve an :class:`~.event.Event` from a Recording.

    :param uri: The URI of the event.
    :return: An event in the recording.

    """
    event = self.get_resource(uri)
    if not isinstance(event, self.EventClass):
      raise KeyError, str(uri)
    return event

  def add_event(self, event):
  #--------------------------
    """
    Add an :class:`~.event.Event` to a Recording.

    :param event: The event to add to the recording.

    """
    event.recording = self
    self.add_resource(event)
    return event

  def new_event(self, uri, etype, at, duration=None, end=None, **kwds):
  #--------------------------------------------------------------------
    """
    Create a new Event and add it to the Recording.

    :return: An Event of type :attr:`EventClass`.
    """
    return self.add_event(self.EventClass(uri, etype, self.interval(at, duration, end), **kwds))


  def instant(self, when):
  #----------------------
    """
    Create an :class:`.Instant` on the recording's timeline.
    """
    return self.timeline.instant(when)

  def interval(self, start, duration=None, end=None):
  #--------------------------------------------------
    """
    Create an :class:`.Interval` on the recording's timeline.
    """
    return self.timeline.interval(start, duration, end=end)


## Or create urn:uuid URIs ??
  def new_segment(self, uri, at, duration=None, end=None, **kwds):  ## Of a Recording
  #---------------------------------------------------------------
    """
    Create a new :class:`~.segment.Segment` of a Recording.

    :param uri: The URI of the Segment.
    :param float at: When the segment starts.
    :param float duration: The duration of the Segment. Optional.
    :param float duration: When the Segment ends. Optional.
    :param kwds: Optional additional attributes for the Segment.

    """
    return self.add_resource(Segment(uri, self, self.interval(at, duration, end), **kwds))


  def save_to_graph(self, graph):
  #------------------------------
    """
    Add a Recording's metadata to a RDF graph.

    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    """
    AbstractObject.save_to_graph(self, graph)
    for resource in self._resources.values():
      resource.save_to_graph(graph)

  @classmethod
  def create_from_graph(cls, uri, graph, signals=True, **kwds):
  #------------------------------------------------------------
    """
    Create a new instance of a Recording, setting attributes from RDF triples in a graph.

    :param uri: The URI for the Recording.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :type signals: Set False to not load the Recording's Signals.
    :rtype: :class:`Recording`
    """
    self = cls(uri, **kwds)
#    self = cls(uri, timeline=graph.get_object(uri, TL.timeline).uri, **kwds)
    self.add_metadata(graph)
    if signals:
      for r in graph.query("select ?s where { ?s a <%s> . ?s <%s> <%s> } order by ?s"
                           % (BSML.Signal, BSML.recording, self.uri)):
        self.add_signal(self.SignalClass.create_from_graph(str(r['s']), graph, units=None))
    # Do we load events? There may be a lot of them...
    self.graph = graph
    return self
