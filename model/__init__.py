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
from biosignalml.rdf import XSD, RDF, RDFS, DCT, TL

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

  attributes = ['recording', 'units', 'transducer', 'filter', '_rate',  '_period', 'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
                'index', 'signaltype', 'offset', 'duration',
               ]
  '''Generic attributes of a Signal.'''

  mapping = { 'recording':    PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              'units':        PropertyMap(BSML.units, to_rdf=mapping.get_uri),
##            'transducer':   PropertyMap(BSML.transducer),
              'filter':       PropertyMap(BSML.preFilter),
              '_rate':        PropertyMap(BSML.rate, XSD.double),
              '_period':      PropertyMap(BSML.period, XSD.double),
              'clock':        PropertyMap(BSML.clock, to_rdf=mapping.get_uri, subelement=True),
              'minFrequency': PropertyMap(BSML.minFrequency, XSD.double),
              'maxFrequency': PropertyMap(BSML.maxFrequency, XSD.double),
              'minValue':     PropertyMap(BSML.minValue, XSD.double),
              'maxValue':     PropertyMap(BSML.maxValue, XSD.double),
              'dataBits':     PropertyMap(BSML.dataBits, XSD.integer),
              'index':        PropertyMap(BSML.index, XSD.integer),
              'signaltype':   PropertyMap(BSML.signalType),
              'offset':       PropertyMap(BSML.offset, XSD.dayTimeDuration,
                                          utils.seconds_to_isoduration,
                                          utils.isoduration_to_seconds),
              'duration':     PropertyMap(DCT.extent, XSD.dayTimeDuration,
                                          utils.seconds_to_isoduration,
                                          utils.isoduration_to_seconds),
            }

  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    rate = kwds.pop('rate', None)
    period = kwds.pop('period', None)
    if rate is not None and period is not None and float(rate) != 1.0/float(period):
      raise ValueError("Signal's sampling rate doesn't match its period")
    kwds['_rate'] = rate
    kwds['_period'] = period
    core.AbstractObject.__init__(self, uri, units=units, **kwds)

  @property
  def rate(self):
  #==============
    if   self._rate   is not None: return float(self._rate)
    elif self._period is not None: return 1.0/float(self._period)

  @property
  def period(self):
  #================
    if   self._period is not None: return float(self._period)
    elif self._rate   is not None: return 1.0/float(self._rate)


class Event(core.AbstractObject):
#================================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event      #: :attr:`.BSML.Event`

  attributes = ['eventtype', 'time', 'recording' ]
  '''Generic attributes of an Event.'''

  mapping = { 'recording': PropertyMap(BSML.recording, to_rdf=mapping.get_uri),
              'eventtype': PropertyMap(BSML.eventType),
              'time':      PropertyMap(BSML.time, subelement=True),
            }

  def __init__(self, uri, eventtype, time=None, **kwds):
  #-----------------------------------------------------
    core.AbstractObject.__init__(self, uri, eventtype=eventtype,
                                            time=time,
                                            **kwds)

  def __str__(self):
  #-----------------
    return 'Event %s at %s' % (self.eventtype, self.time)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    from biosignalml.data.time import TemporalEntity  # Prevent a circular import
    self = cls(uri, None, **kwds)
    self.load_from_graph(graph)
    if self.time is not None:
      self.time = TemporalEntity.create_from_graph(self.time, graph)
    return self


def _get_timeline(tl):      # Stops a circular import
#--------------------
  from biosignalml.data.time import RelativeTimeLine
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

  mapping = { 'format':        PropertyMap(DCT.format),
              'dataset':       PropertyMap(BSML.dataset),
              'source':        PropertyMap(DCT.source),
              'investigation': PropertyMap(DCT.subject),
              'starttime':     PropertyMap(DCT.created, XSD.dateTime,
                                           utils.datetime_to_isoformat,
                                           utils.isoformat_to_datetime),
              'duration':      PropertyMap(DCT.extent, XSD.dayTimeDuration,
                                           utils.seconds_to_isoduration,
                                           utils.isoduration_to_seconds),
##            'digest':        PropertyMap(BSML.digest),
              'timeline':      PropertyMap(TL.timeline,
                                           to_rdf=mapping.get_uri,
                                           from_rdf=_get_timeline, subelement=True) }

  SignalClass = Signal       #: The class of Signals in the Recording


  def __init__(self, uri, **kwds):
  #-------------------------------
    from biosignalml.data.time import RelativeTimeLine   ## Otherwise circular import...
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

    .. note:: If indices are to be useful they must be a permanent attribute and held in RDF.

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
    :param units: The units signal values are in.
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

  def new_event(self, uri, etype, at, duration=None, end=None, **kwds):
  #--------------------------------------------------------------------
    evt = Event(uri, etype, self.interval(at, duration, end), **kwds)
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
      dct:creator <someone> ;
      dct:created "2012-09-29T09:30:23Z"^^xsd:dateTime ;
      .

  The <target> may refer to instant or interval on a recording or signal
  by including a media fragment with the URI (see
  http://www.w3.org/TR/media-frags/#URIquery-vs-fragments).


  Do we have 'time' as an attribute and map to/from media fragments?

  Best to let caller do this?? And utils package to have helper functions.

  '''
  metaclass = BSML.Annotation  #: :attr:`.BSML.Annotation`

  attributes = [ 'about', 'comment', 'tags', 'time', 'creator', 'created' ]

  mapping = { 'about':   PropertyMap(DCT.subject, to_rdf=mapping.get_uri),
              'comment': PropertyMap(RDFS.comment),
              'tags':    PropertyMap(BSML.tag),
              'time':    PropertyMap(BSML.time, subelement=True),
              'creator': PropertyMap(DCT.creator, to_rdf=mapping.get_uri),
              'created': PropertyMap(DCT.created, XSD.dateTime,
                                     utils.datetime_to_isoformat,
                                     utils.isoformat_to_datetime),
            }


  def __init__(self, uri, about=None, comment=None, tags=None, time=None, creator=None, timestamp=True, **kwds):
  #-------------------------------------------------------------------------------------------------------------
    if time is not None: assert(time.end >= time.start)   ###
    created = kwds.pop('created', utils.utctime()) if timestamp else None
    label = kwds.get('label', '')
    core.AbstractObject.__init__(self, uri, about=about, comment=comment, time=time,
      creator=creator, created=created, **kwds)
    self.tags = tags if tags else []

  @classmethod
  def Note(cls, uri, about, text, time=None, **kwds):
  #--------------------------------------------------
    return cls(uri, about, comment=text, time=time, **kwds)

  @classmethod
  def Tag(cls, uri, about, tag, time=None, **kwds):
  #------------------------------------------------
    return cls(uri, about, tags=[tag], time=time, **kwds)

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
    from biosignalml.data.time import TemporalEntity  # Prevent a circular import
    self = cls(uri, timestamp=False, **kwds)
    self.load_from_graph(graph)
    if self.time is not None:
      self.time = TemporalEntity.create_from_graph(self.time, graph)
    return self


if __name__ == '__main__':
#=========================

  logging.getLogger().setLevel('DEBUG')

  def print_dict(r):
  #-----------------
    print '{'
    for kv in r.__dict__.iteritems(): print '  %s: %s' % kv
    print '  }'

  def check(instance):
  #-------------------
    g = rdf.Graph()
    instance.save_to_graph(g)
#    print g.serialise(format=rdf.Format.TURTLE)
    copy = instance.__class__.create_from_graph(instance.uri, g)
#    if isinstance(instance, Event):
#      print_dict(instance.about)
#      print_dict(copy.about)
#    print instance.metadata_as_string(rdf.Format.TURTLE)
#    print copy.metadata_as_string(rdf.Format.TURTLE)
    if instance.metadata_as_string(rdf.Format.TURTLE) != copy.metadata_as_string(rdf.Format.TURTLE):
      print "INPUT:", instance.metadata_as_string(rdf.Format.TURTLE)
      print "RESULT:", copy.metadata_as_string(rdf.Format.TURTLE)
      raise AssertionError
    return copy


  r1 = Recording('http://example.org/recording', duration='1806')
#  r1 = 'http://example.org/rec1'
#  print r1.metadata_as_string(rdf.Format.TURTLE)

#  a1 = Annotation.Note('http://example.org/ann1', r1, 'comment', creator='dave')
  e1 = Annotation.Note('http://example.org/event', r1, 'event', r1.interval(1, 0.5),
     creator='dave')
  t1 = Annotation.Tag('http://example.org/tag1', r1, 'tag')
#  print t1.metadata_as_string(rdf.Format.TURTLE)
#  for t in t1.tags: print (str(t))

#  r2 = check(r1)
#  a2 = check(a1)
#  print a2.metadata_as_string(rdf.Format.TURTLE)

  e2 = check(e1)
#  print e2.metadata_as_string(rdf.Format.TURTLE)

#  assert(e2.time == e1.time)

#  t2 = check(t1)
#  print t2.metadata_as_string(rdf.Format.TURTLE)
#  for t in t2.tags: print (str(t))

  ev1 = r1.new_event('http://ex.org/evt1', 'etype', 32.0, 10)
#  print ev1.metadata_as_string(rdf.Format.TURTLE)
  ev2 = check(ev1)

  ev1 = r1.new_event('http://ex.org/evt1', 'etype', 32.0)
#  print ev1.metadata_as_string(rdf.Format.TURTLE)
  ev2 = check(ev1)


