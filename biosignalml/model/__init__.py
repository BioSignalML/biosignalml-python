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
from collections import OrderedDict

import biosignalml.rdf as rdf
import biosignalml.utils as utils
import biosignalml.units as units
from biosignalml.ontology import BSML
from biosignalml.rdf import XSD, RDF, RDFS, DCT, TL, PROV

from .core import AbstractObject
from .mapping import PropertyMap


from .segment    import Segment

from .annotation import Annotation


def makelabel(label, suffix):
#============================
  """
  Helper function to generate a meaningful label for sub-properties of resources.

  :param label: The label of some resource.
  :param suffix: A suffix to append to the label.
  :return: A string consisting of the label, a '_', and the suffix.
  """
  return label + '_' + suffix


class Signal(AbstractObject):
#============================
  """
  An abstract BioSignalML Signal.

  :param uri: The URI of the signal.
  :param units: The physical units of the signal's data.
  """

  metaclass = BSML.Signal     #: :attr:`.BSML.Signal`

  attributes = ['recording', 'units', 'transducer', 'filter', '_rate',  '_period', 'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
                'index', 'signaltype', 'offset', '_duration',
               ]
  '''Generic attributes of a Signal.'''

  mapping = { 'recording':    PropertyMap(BSML.recording, to_rdf=PropertyMap.get_uri),
              'units':        PropertyMap(BSML.units, to_rdf=PropertyMap.get_uri),
##            'transducer':   PropertyMap(BSML.transducer),
              'filter':       PropertyMap(BSML.preFilter),
              '_rate':        PropertyMap(BSML.rate, XSD.double),
              '_period':      PropertyMap(BSML.period, XSD.double),
              'clock':        PropertyMap(BSML.clock, to_rdf=PropertyMap.get_uri, subelement=True),
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
              '_duration':    PropertyMap(DCT.extent, XSD.dayTimeDuration,
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
    AbstractObject.__init__(self, uri, units=units, **kwds)

  def __len__(self):
  #----------------
    return 0

  def __nonzero__(self):
  #---------------------
    return True  # Otherwise bool(sig) is False, because we have __len__()

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

  @property
  def duration(self):
  #------------------
    if self._duration is not None: return self._duration
    elif self.period is not None: return len(self)*self.period
    ## self.time[-1] + (self.period if self.period is not None else 0)  ???

  @property
  def time_units(self):
  #====================
    return units.get_units_uri('s')


class Event(AbstractObject):
#===========================
  '''
  An abstract BioSignalML Event.
  '''

  metaclass = BSML.Event      #: :attr:`.BSML.Event`

  attributes = ['eventtype', 'time', 'recording', 'index' ]
  '''Generic attributes of an Event.'''

  mapping = { 'recording': PropertyMap(BSML.recording, to_rdf=PropertyMap.get_uri),
              'eventtype': PropertyMap(BSML.eventType),
              'time':      PropertyMap(BSML.time, subelement=True),
              'index':     PropertyMap(BSML.index, XSD.integer),
            }

  def __init__(self, uri, eventtype, time=None, **kwds):
  #-----------------------------------------------------
    if time is not None: assert(time.end >= time.start)
    AbstractObject.__init__(self, uri, eventtype=eventtype, time=time, **kwds)

  def __str__(self):
  #-----------------
    return 'Event %s at %s' % (self.eventtype, self.time)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    from biosignalml.data.time import TemporalEntity  # Prevent a circular import
    self = cls(uri, None, **kwds)
    self.add_metadata(graph)
    if self.time is not None:
      self.time = TemporalEntity.create_from_graph(self.time, graph)
    return self


def _get_timeline(tl):      # Stops a circular import
#--------------------
  from biosignalml.data.time import RelativeTimeLine
  return RelativeTimeLine(tl)


class Recording(AbstractObject):
#===============================
  '''
  An abstract BioSignalML Recording.

  :param uri: The URI of the recording.
  '''

  metaclass = BSML.Recording  #: :attr:`.BSML.Recording`

  attributes = [ 'dataset', 'source', 'format', 'comment', 'investigation',
                 'starttime', 'duration', 'timeline', 'generatedBy'
               ]
  '''Generic attributes of a Recording.'''

  mapping = { 'format':        PropertyMap(DCT.format),
              'dataset':       PropertyMap(BSML.dataset),
              'source':        PropertyMap(DCT.source, functional=False),
              'investigation': PropertyMap(DCT.subject),
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

  SignalClass = Signal       #: The class of Signals in the Recording
  EventClass  = Event        #: The class of Events in the Recording


  def __init__(self, uri, **kwds):
  #-------------------------------
    from biosignalml.data.time import RelativeTimeLine   ## Otherwise circular import...
    AbstractObject.__init__(self, uri, **kwds)
    self.timeline = RelativeTimeLine(str(uri) + '/timeline')
    self._resources = OrderedDict()

  def add_resource(self, resource):
  #--------------------------------
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
    return self._resources[str(uri)]


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
    Retrieve a :class:`Signal` from a Recording.

    :param uri: The URI of the signal to get.
    :return: A signal in the recording.
    :rtype: :class:`Signal`
    """
    signal = self.get_resource(uri)
    if not isinstance(signal, self.SignalClass):
      raise KeyError, str(uri)
    return signal

  def add_signal(self, signal):
  #----------------------------
    """
    Add a :class:`Signal` to a Recording.

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
    event = self.get_resource(uri)
    if not isinstance(event, self.EventClass):
      raise KeyError, str(uri)
    return event

  def add_event(self, event):
  #--------------------------
    event.recording = self
    self.add_resource(event)
    return event

  def new_event(self, uri, etype, at, duration=None, end=None, **kwds):
  #--------------------------------------------------------------------
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
    return self.make_resource(Segment(uri, self, self.interval(at, duration, end), **kwds))

  def new_segment(self, uri, at, duration=None, end=None, **kwds):  ## Of a Signal
  #---------------------------------------------------------------
    return self.recording.make_resource(Segment(uri, self, self.interval(at, duration, end), **kwds))


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
  e1 = Annotation.Note('http://example.org/event', Segment(r1, r1.interval(1, 0.5)),
     'event',
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


