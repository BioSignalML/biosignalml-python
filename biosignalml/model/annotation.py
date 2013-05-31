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

from biosignalml.rdf import RDFS, DCT
import biosignalml.utils as utils

from .ontology import BSML
from .core     import AbstractObject
from .mapping  import PropertyMap
from .segment  import Segment

__all__ = [ 'Annotation' ]


class Annotation(AbstractObject):
#================================
  """
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

  """
  ### This (or core.AbstractObject ??) needs to detect a prior version exists
  ### and link versions... cf. QtBrowser annotation edit/delete...
  ###
  ### An update or replace or ? method?? With auto URI generation ???
  ###
  metaclass = BSML.Annotation                  #: :attr:`.BSML.Annotation`

  attributes = [ 'about', 'comment', 'tags' ]  #: Attributes of an Annotation.

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
    """
    Create a new instance of an Annotation, setting attributes from RDF triples in a graph.

    :param uri: The URI of the Annotation.
    :param graph: A RDF graph.
    :type graph: :class:`~biosignalml.rdf.Graph`
    :rtype: :class:`Annotation`
    """
    self = cls(uri, timestamp=False, **kwds)
    self.add_metadata(graph)
    if graph.has_resource(self.about, BSML.Segment):
      self.about = Segment.create_from_graph(self.about, graph)
    return self

  @property
  def time(self):
  #--------------
    """The time, if any, associated with the resource that is annotated."""
    if isinstance(self.about, Segment):
      return self.about.time
