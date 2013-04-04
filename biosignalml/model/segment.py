import logging

from biosignalml import BSML
from biosignalml.rdf import RDFS, DCT
import biosignalml.utils as utils
import biosignalml.rdf as rdf

from .core import AbstractObject
from .mapping import PropertyMap


class Segment(AbstractObject):
#=============================
  """
  An named temporal segment of a Recording or Signal.

  A Segment is described in RDF as:::

    <segment> a bsml:Segment ;
      bsml:segment <resource> ;
      bsml:time <temporal_entity> ;
      .

  """
  metaclass = BSML.Segment  #: :attr:`.BSML.Segment

  attributes = [ 'source', 'time' ]

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
    if self.time is not None:
      self.time = TemporalEntity.create_from_graph(self.time, graph)
    return self
