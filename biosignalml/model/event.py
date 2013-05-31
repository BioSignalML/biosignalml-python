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
A BioSignalML Event.
"""

import logging

import biosignalml.utils as utils

from .ontology import BSML
from .core     import AbstractObject
from .mapping  import PropertyMap

__all__ = [ 'Event' ]


class Event(AbstractObject):
#===========================
  """
  An abstract BioSignalML Event.
  """

  metaclass = BSML.Event                            #: :attr:`.BSML.Event`

  attributes = ['eventtype', 'time', 'recording' ]  #: Generic attributes of an Event.

  mapping = { 'recording': PropertyMap(BSML.recording, to_rdf=PropertyMap.get_uri),
              'eventtype': PropertyMap(BSML.eventType),
              'time':      PropertyMap(BSML.time, subelement=True),
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

