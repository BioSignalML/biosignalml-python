'''
RelativeTimeLine, Instant and Interval objects.
'''
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


import biosignalml.rdf as rdf
from biosignalml.rdf import RDF, RDFS, DCT, XSD, TL

import biosignalml.utils as utils
import biosignalml.model as model
from biosignalml.model import BSML
from biosignalml.model.mapping import PropertyMap

__all__ = [ 'Instant', 'Interval', 'RelativeTimeLine', 'TemporalEntity' ]


class RelativeTimeLine(model.core.AbstractObject):
#=================================================

  '''
  An abstract BioSignalML TimeLine.
  '''

  metaclass = TL.RelativeTimeLine  #: :attr:`.TL.RelativeTimeLine`

  def instant(self, when):
  #----------------------
    return Instant(self.make_uri(), when, self)

  def interval(self, start, duration=None, end=None):
  #--------------------------------------------------
    if duration in [0, None] and end is None: return self.instant(start)
    else:                                     return Interval(self.make_uri(), start, duration, self, end)



class TemporalEntity(model.core.AbstractObject):
#===============================================
  '''
  An abstract Temporal Entity.

  The superclass of Intervals and Instants.
  '''
  attributes = [ 'timeline', 'start' ]

  mapping = { 'timeline': PropertyMap(TL.timeline,
                                      to_rdf=PropertyMap.get_uri,
                                      from_rdf=RelativeTimeLine) }

  @classmethod
  def create(cls, uri, start, duration=None, end=None, **kwds):
  #------------------------------------------------------------
    if duration in [None, 0.0] and end in [None, start]:
      return Instant(uri, start, **kwds)
    else:
      return Interval(uri, start, duration=duration, end=end, **kwds)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    """
    We can't call the 'create_from_graph()' for the appropriate
    class as leads to recursion...
    """
    self = None
    if   graph.contains(rdf.Statement(uri, RDF.type, Interval.metaclass)):
      self = Interval(uri, None, **kwds)
    elif graph.contains(rdf.Statement(uri, RDF.type, Instant.metaclass)):
      self = Instant(uri, None, **kwds)
    if self is not None:
      self.add_metadata(graph)
      self.graph = graph
    return self


class Interval(TemporalEntity):
#==============================
  '''
  An abstract BioSignalML Interval.

  We assume intervals are topologically semi-open -- ``end`` is just outside.
  '''

  metaclass = BSML.Interval #: :attr:`.BSML.Interval` owl:sameAs tl:RelativeInterval

  attributes = [ 'duration' ]

  mapping = { 'start':    PropertyMap(TL.start, XSD.dayTimeDuration,
                                      utils.seconds_to_isoduration,
                                      utils.isoduration_to_seconds),
              'duration': PropertyMap(TL.duration, XSD.dayTimeDuration,
                                      utils.seconds_to_isoduration,
                                      utils.isoduration_to_seconds) }

  def __init__(self, uri, start, duration=None, timeline=None, end=None, **kwds):
  #------------------------------------------------------------------------------
    assert(end is None or start <= end)
    super(Interval, self).__init__(uri, start=start,
                                   duration=duration if end is None else (end-start),
                                   timeline=timeline,
                                   **kwds)

  @property
  def end(self, timeline=None):     # Needs to use timeline to map
  #----------------------------
    '''Get the end of the interval.'''
    return self.start + (self.duration if self.duration is not None else 0.0)

  def __add__(self, increment):
  #----------------------------
    return Interval(self.make_uri(True), self.start + increment, self.duration, self.timeline)

  def __eq__(self, interval):
  #--------------------------
    if interval is None or not isinstance(interval, Interval): return False
    d1 = self.duration     if self.duration     is not None else 0
    d2 = interval.duration if interval.duration is not None else 0
    return self.start == interval.start and d1 == d2

  def __str__(self):
  #-----------------
    return 'Interval: %g for %g' % (self.start, self.duration)


class Instant(TemporalEntity):
#=============================
  '''
  An abstract BioSignalML Instant.
  '''

  metaclass = BSML.Instant  #: :attr:`.BSML.Instant` owl:sameAs tl:RelativeInstant

  mapping = { 'start': PropertyMap(TL.at, XSD.dayTimeDuration,
                                   utils.seconds_to_isoduration,
                                   utils.isoduration_to_seconds) }

  def __init__(self, uri, when, timeline=None, **kwds):
  #----------------------------------------------------
    super(Instant, self).__init__(uri, start=when, timeline=timeline, **kwds)
    self.duration = None
    self.end = self.start

  def __add__(self, increment):
  #----------------------------
    return Instant(self.make_uri(True), self.at + increment, self.timeline)

  def __eq__(self, instant):
  #-------------------------
    return (instant is not None and isinstance(instant, Instant)
        and self.start == instant.start)

  def __str__(self):
  #-----------------
    return 'Instant: %g' % self.start
