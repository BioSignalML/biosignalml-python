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

import logging

from biosignalml.rdf import DCT

from .ontology import BSML
from .core     import AbstractObject
from .mapping  import PropertyMap

__all__ = [ 'Segment' ]


class Segment(AbstractObject):
#=============================
  """
  An named temporal segment of a Recording or Signal.

  A Segment is described in RDF as:::

    <segment> a bsml:Segment ;
      bsml:segment <resource> ;
      bsml:time <temporal_entity> ;
      .


  :param uri: The URI of the segment.
  :param source: The resource (Signal or Recording) which the Segment is part of.
  :param time: A :class:`.TemporalEntity` locating the Segment in its resource.
  :param kwds: Segment attributes, specified as keywords.

  """
  metaclass = BSML.Segment            #: :attr:`.BSML.Segment`

  attributes = [ 'source', 'time' ]   #: Attributes of a Segment.

  mapping = { 'source': PropertyMap(DCT.source, to_rdf=PropertyMap.get_uri),
              'time':   PropertyMap(BSML.time, subelement=True),
            }


  def __init__(self, uri, source=None, time=None, **kwds):
  #-------------------------------------------------------
    if time is not None: assert(time.end >= time.start)
    AbstractObject.__init__(self, uri, source=source, time=time, **kwds)

  def __str__(self):
  #-----------------
    return 'Segment %s of %s' % (self.time, self.source)

  @classmethod
  def create_from_graph(cls, uri, graph, **kwds):
  #----------------------------------------------
    '''
    Create a new instance of a Segment, setting attributes from RDF triples in a graph.

    :param uri: The URI of the Segment.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`Segment`
    '''
    from biosignalml.data.time import TemporalEntity  # Prevent a circular import
    self = cls(uri, **kwds)
    self.add_metadata(graph)
    if self.time is not None:  ## Could add_metadata automatically do this for sub-elements??
                               ## PropertyMap would need to know class (TemporalEntity)
      self.time = TemporalEntity.create_from_graph(self.time, graph)
    return self
