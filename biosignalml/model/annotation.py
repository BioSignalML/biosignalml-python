import logging

from biosignalml import BSML
from biosignalml.rdf import RDFS, DCT
import biosignalml.utils as utils

from .core import AbstractObject
from .mapping import PropertyMap
from .segment import Segment


class Annotation(AbstractObject):
#================================
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

  '''
  metaclass = BSML.Annotation  #: :attr:`.BSML.Annotation

  attributes = [ 'about', 'comment', 'tags' ]

  mapping = { 'about':   PropertyMap(DCT.subject, to_rdf=PropertyMap.get_uri),
              'comment': PropertyMap(RDFS.comment),
              'tags':    PropertyMap(BSML.tag, functional=False),
            }

  def __init__(self, uri, about=None, comment=None, tags=None, timestamp=True, **kwds):
  #------------------------------------------------------------------------------------
    created = kwds.pop('created', utils.utctime()) if timestamp else None
    AbstractObject.__init__(self, uri, about=about, comment=comment, created=created, **kwds)
    self.tags = tags if tags else []

  @classmethod
  def Note(cls, uri, about, text, **kwds):
  #---------------------------------------
    return cls(uri, about, comment=text, **kwds)

  @classmethod
  def Tag(cls, uri, about, tag, **kwds):
  #-------------------------------------
    return cls(uri, about, tags=[tag], **kwds)

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
    self = cls(uri, timestamp=False, **kwds)
    self.add_metadata(graph)
    if graph.has_resource(self.about, BSML.Segment):
      self.about = Segment.create_from_graph(self.about, graph)
    return self

  @property
  def time(self):
  #--------------
    logging.debug("ABT: %s", repr(self.about))
    if isinstance(self.about, Segment):
      return self.about.time
