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
import re

import biosignalml.utils as utils
import biosignalml.rdf as rdf
from biosignalml.ontology import BSML
from biosignalml.rdf import XSD, RDF, RDFS, DCTERMS, TL

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

  attributes = ['recording', 'units', 'transducer', 'filter', 'rate',  'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
                'index', 'signaltype', 'offset', 'duration',
               ]
  '''Generic attributes of a Signal.'''

  mapping = { ('recording',    None): PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              ('units',        None): PropertyMap(BSML.units, to_rdf=mapping.get_uri),
##            ('transducer',   None): PropertyMap(BSML.transducer),
              ('filter',       None): PropertyMap(BSML.preFilter),
              ('rate',         None): PropertyMap(BSML.rate, XSD.double),
              ('clock',        None): PropertyMap(BSML.clock, to_rdf=mapping.get_uri),
              ('minFrequency', None): PropertyMap(BSML.minFrequency, XSD.double),
              ('maxFrequency', None): PropertyMap(BSML.maxFrequency, XSD.double),
              ('minValue',     None): PropertyMap(BSML.minValue, XSD.double),
              ('maxValue',     None): PropertyMap(BSML.maxValue, XSD.double),
              ('dataBits',     None): PropertyMap(BSML.dataBits, XSD.integer),
              ('index',        None): PropertyMap(BSML.index, XSD.integer),
              ('signaltype',   None): PropertyMap(BSML.signalType),
              ('offset',       None): PropertyMap(BSML.offset, XSD.dayTimeDuration,
                                                  utils.seconds_to_isoduration,
                                                  utils.isoduration_to_seconds),
              ('duration',     None): PropertyMap(DCTERMS.extent, XSD.dayTimeDuration,
                                                  utils.seconds_to_isoduration,
                                                  utils.isoduration_to_seconds),
            }

  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    core.AbstractObject.__init__(self, uri, units=units, **kwds)


class Event(core.AbstractObject):
#================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event      #: :attr:`.BSML.Event`

  attributes = ['eventtype', 'time', 'duration' ]
  '''Generic attributes of an Event.'''

  mapping = { ('recording', None): PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              ('eventtype', None): PropertyMap(BSML.eventType),
              ('time',      None): PropertyMap(BSML.offset, XSD.dayTimeDuration,
                                               utils.seconds_to_isoduration,
                                               utils.isoduration_to_seconds),
              ('duration',  None): PropertyMap(DCTERMS.extent, XSD.dayTimeDuration,
                                               utils.seconds_to_isoduration,
                                               utils.isoduration_to_seconds),
            }

  def __init__(self, uri, eventtype, time=None, duration=None, end=None, **kwds):
  #--------------------------------------------------------------------------
    core.AbstractObject.__init__(self, uri, eventtype=eventtype,
                                            time=time,
                                            duration=duration if end is None else (end-time),
                                            **kwds)
    self.recording = None

  def __str__(self):
  #-----------------
    return 'Event %s at %s' % (self.eventtype, self.time)


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

  attributes = [ 'dataset', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration', 'timeline'
               ]
  '''Generic attributes of a Recording.'''

  mapping = { ('format',        metaclass): PropertyMap(DCTERMS.format),
              ('dataset',       metaclass): PropertyMap(BSML.dataset),
              ('source',        metaclass): PropertyMap(DCTERMS.source),
              ('investigation', metaclass): PropertyMap(DCTERMS.subject),
              ('starttime',     metaclass): PropertyMap(DCTERMS.created, XSD.dateTime,
                                                        utils.datetime_to_isoformat,
                                                        utils.isoformat_to_datetime),
              ('duration',      metaclass): PropertyMap(DCTERMS.extent, XSD.dayTimeDuration,
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
    if signal.recording:     ## Set from RDF mapping...
      if isinstance(signal.recording, Recording): rec_uri = signal.recording.uri
      else:                                       rec_uri = signal.recording
      if str(rec_uri) != str(self.uri):
        raise Exception, "Adding to '%s', but signal '%s' is in '%s'" % (self.uri, sig_uri, rec_uri)
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
    return self._events.values()

  def add_event(self, event):
  #--------------------------
    event.recording = self
    self._events[str(event.uri)] = event

  def new_event(self, uri, etype, **kwds):
  #---------------------------------------
    evt = Event(uri, etype, **kwds)
    self.add_event(evt)
    return evt

  def get_event(self, uri):
  #------------------------
    return self._events[str(uri)]


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
    self.load_from_graph(graph)
    if signals:
      for r in graph.query("select ?s where { ?s a <%s> . ?s <%s> <%s> } order by ?s"
                           % (BSML.Signal, BSML.recording, self.uri)):
        self.add_signal(self.SignalClass.create_from_graph(str(r['s']), graph, units=None))
    # Do we load events? There may be a lot of them...
    self.graph = graph
    return self


class Annotation(core.AbstractObject):
#=====================================
  '''
  An abstract BioSignalML Annotation.

  An Annotation is a comment about something made by someone. In BioSignalML
  we use the following model:::

    <annotation> a bsml:Annotation ;
      bsml:about <target> ;
      rdfs:comment "a comment" ;        # Optional if there are tags
      bsml:tag <a/semantic/tag> ;       # Zero or more
      dcterms:creator <someone> ;
      dcterms:created "2012-09-29T09:30:23Z"^^xsd:dateTime ;
      .

  The <target> may refer to instant or interval on a recording or signal
  by including a media fragment with the URI (see
  http://www.w3.org/TR/media-frags/#URIquery-vs-fragments).


  Do we have 'time' as an attribute and map to/from media fragments?

  Best to let caller do this?? And utils package to have helper functions.

  '''
  metaclass = BSML.Annotation  #: :attr:`.BSML.Annotation`

  attributes = [ 'about', 'comment', 'tags', 'creator', 'created' ]

  mapping = { ('about',   None): PropertyMap(DCTERMS.subject, to_rdf=mapping.get_uri),
              ('comment', None): PropertyMap(RDFS.comment),
              ('tags',    None): PropertyMap(BSML.tag),
              ('creator', None): PropertyMap(DCTERMS.creator, to_rdf=mapping.get_uri),
              ('created', None): PropertyMap(DCTERMS.created, XSD.dateTime,
                                               utils.datetime_to_isoformat,
                                               utils.isoformat_to_datetime),
            }


  def __init__(self, uri, about=None, text=None, tags=None, creator=None, set_time=True, **kwds):
  #----------------------------------------------------------------------------------------------
    created = kwds.pop('created', utils.utctime()) if set_time else None
    label = kwds.get('label', '')
    core.AbstractObject.__init__(self, uri, about=about, comment=text, creator=creator, created=created, **kwds)
    self.tags = tags if tags else []
    self._time = None

  @classmethod
  def Note(cls, uri, about, text, **kwds):
  #---------------------------------------
    return cls(uri, about, text=text, **kwds)

  @classmethod
  def Tag(cls, uri, about, tag, **kwds):
  #-------------------------------------
    return cls(uri, about, tags=[tag], **kwds)

  @classmethod
  def Event(cls, uri, about, time, **kwds):
  #----------------------------------------
    self = cls(uri, '%s#t=%g,%g' % (about.uri, time.start, time.end), **kwds)
    self._time= time
    return self

  def tag(self, tag):
  #------------------
    self.tags.append(tag)

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
    mtag = str(self.about).rfind('#t=')
    if mtag >= 0:
      from biosignalml.timeline import Instant, Interval
      try:
        times = re.match('(.*?)(,(.*))?$', str(self.about)[mtag+3:]).groups()
        start = float(times[0]) if times[0] else 0.0
        end = float(times[2])
        self._time = Instant(None, start) if start == end else Interval(None, start, end=end)
      except ValueError:
        pass
    return self

  @property
  def time(self):
  #--------------
    return self._time


if __name__ == '__main__':
#=========================

  def print_dict(r):
  #-----------------
    print '{'
    for kv in r.__dict__.iteritems(): print '  %s: %s' % kv
    print '  }'

  def check(instance):
  #-------------------
    g = rdf.Graph()
    instance.save_to_graph(g)
    copy = instance.__class__.create_from_graph(instance.uri, g)
#    if isinstance(instance, Event):
#      print_dict(instance.about)
#      print_dict(copy.about)
#    print instance.metadata_as_string(rdf.Format.TURTLE)
#    print copy.metadata_as_string(rdf.Format.TURTLE)
    assert(instance.metadata_as_string(rdf.Format.TURTLE) == copy.metadata_as_string(rdf.Format.TURTLE))
    return copy


  r1 = Recording('http://example.org/recording', duration='1806')
#  print r1.metadata_as_string(rdf.Format.TURTLE)

  a1 = Annotation.Note('http://example.org/ann1', r1, 'comment', creator='dave')
  e1 = Annotation.Event('http://example.org/event', r1, r1.interval(1, 0.5),
     creator='dave', text='event text')
#  print e1.metadata_as_string(rdf.Format.TURTLE)

  r2 = check(r1)
  a2 = check(a1)
#  print a2.metadata_as_string(rdf.Format.TURTLE)

  e2 = check(e1)
  print e2.metadata_as_string(rdf.Format.TURTLE)

  assert(e2.time == e1.time)

  ev1 = r1.new_event('http://ex.org/evt1', a1, time=32.3)
  print ev1.metadata_as_string(rdf.Format.TURTLE)

