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
BSML Store description...

"""

import logging
import operator

import biosignalml.formats
from biosignalml import BSML, Recording, Signal, Event, Annotation, Segment
from biosignalml.data.time import TemporalEntity
from biosignalml.rdf import RDFS, DCT, PRV, TL, Format
import biosignalml.rdf.sparqlstore as sparqlstore

from .graphstore import GraphStore, GraphUpdate

__all__ = [ 'BSMLStore', 'BSMLUpdateStore' ]


'''Graph holding bsml:SemanticTag resources.'''
SEMANTIC_TAGS = 'http://ontologies.biosignalml.org/semantic-tags'


class BSMLStore(GraphStore):
#===========================
  '''
  An RDF repository containing BioSignalML metadata.
  '''

  def __init__(self, base_uri, sparqlstore):
  #-----------------------------------------
    GraphStore.__init__(self, base_uri, BSML.RecordingGraph, sparqlstore)

  def has_recording(self, uri):
  #----------------------------
    ''' Check a URI refers to a Recording. '''
    return self.has_resource(uri, BSML.Recording)

  def has_signal(self, uri, graph_uri=None):
  #-----------------------------------------
    ''' Check a URI refers to a Signal. '''
    return self.has_resource(uri, BSML.Signal, graph_uri)

  def has_signal_in_recording(self, sig, rec):
  #-------------------------------------------
    ''' Check a URI refers to a Signal in a given Recording. '''
    g, r = get_graph_and_recording_uri(rec)
    return g is not none and self.has_signal(sig, g)

  def recording_uris(self):
  #------------------------
    """
    Return a list of recording URIs in the repository.

    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    """
    return [ r[1] for r in self.get_resources(BSML.Recording) ]

  def get_graph_and_recording_uri(self, uri):
  #------------------------------------------
    """
    Get URIs of the Graph and Recording that contain the object.

    :param uri: The URI of some object.
    :return: The tuple (graph_uri, recording_uri)
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    r = self.get_resources(BSML.Recording, condition='<%s> a []' % uri)
    return r[0] if r else (None, None)

  def get_recording(self, uri, with_signals=True, open_dataset=True, recording_class=None,
  #---------------------------------------------------------------------------------------
                                                                     graph_uri=None, **kwds):
    """
    Get the Recording from the graph that an object is in.

    :param uri: The URI of some object.
    :paran with_signals: Default action is to also load the Recording's Signals.
    :param open_dataset: Default action is to open the Recording's dataset.
    :param recording_class: The class of Recording to create. If not set
      the class is determined by the recording's dct:format attribute.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    """
    #logging.debug('Getting: %s', uri)
    if graph_uri is None: graph_uri, rec_uri = self.get_graph_and_recording_uri(uri)
    else: rec_uri = uri
    #logging.debug('Graph: %s', graph_uri)
    if graph_uri is not None:
      if recording_class is None:
        recording_class = biosignalml.formats.CLASSES.get(
                            str(self.get_objects(rec_uri, DCT.format, graph=graph_uri)[0]),
                            Recording)
      graph = self.get_resource_as_graph(rec_uri, BSML.Recording, graph_uri)
##    graph = self.get_graph(graph_uri, BSML.Recording)
      rec = recording_class.create_from_graph(rec_uri, graph, signals=False, **kwds)
      if rec is not None:
        if with_signals:
          for r in self.select('?s', '?s a bsml:Signal . ?s bsml:recording <%(rec)s>',
              params=dict(rec=rec.uri), prefixes=dict(bsml=BSML.prefix),
              graph=graph.uri, order='?s'):
            sig_uri = sparqlstore.get_result_value(r, 's')
            sig_graph = self.get_resource_as_graph(sig_uri, BSML.Signal, rec.graph.uri)
            rec.add_signal(rec.SignalClass.create_from_graph(sig_uri, sig_graph, units=None))
        rec.initialise(open_dataset=open_dataset)    ## This will open files...
      return rec

  def get_signal(self, uri, graph_uri=None, signal_class=None, **kwds):
  #--------------------------------------------------------------------
    '''
    Get a Signal from the repository.

    :param uri: The URI of a Signal.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Signal`
    '''
    ### This assumes all signals for a recording in the repository
    ### have been loaded against the Recording...
    if graph_uri is None: graph_uri = self.get_graph_and_recording_uri(uri)[0]
    graph = self.get_resource_as_graph(uri, BSML.Signal, graph_uri)
    if graph is None: return None

    ## Have to get class of signal's recording...
    if signal_class is None: signal_class = Signal

    return signal_class.create_from_graph(uri, graph, units=None, **kwds)  # units set from graph...

  def signals(self, rec_uri, graph_uri=None):
  #------------------------------------------
    '''
    Return a list of all Signals of a recording.

    :param uri: The URI of the recording.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: list of bsml:Signal URIs
    '''
    return [ r[1]
      for r in self.get_resources(BSML.Signal, rvars='?r',
        condition='?r bsml:recording <%s>' % rec_uri,
        prefixes = dict(bsml=BSML.prefix),
        graph = graph_uri
        ) ]


  def get_event(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get an Event from the repository.

    :param uri: The URI of an Eventt.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Event`
    '''
    # The following line works around a Virtuoso problem
    if graph_uri is None: graph_uri = self.get_graph_and_recording_uri(uri)[0]
    graph = self.get_resource_as_graph(uri, BSML.Event, graph_uri)

##### Put into Event.load_from_graph()   ????
    for tm in graph.get_objects(uri, BSML.time):  ## This could be improved...
      graph.append_graph(self.get_resource_as_graph(tm.uri, BSML.Instant, graph_uri))
      graph.append_graph(self.get_resource_as_graph(tm.uri, BSML.Interval, graph_uri))
    return Event.create_from_graph(uri, graph)

  def get_event_uris(self, rec_uri, eventtype=None, timetype=None, graph_uri=None):
  #--------------------------------------------------------------------------------
    '''
    Return a list of Event URIs associated with a recording.

    :param uri: The URI of the recording.
    :param eventtype: The type of events to find. Optional.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: list of bsml:Event URIs
    '''

    if eventtype is None:
      condition =  '?r bsml:recording <%s>' % rec_uri
    else:
      condition = ('?r bsml:recording <%s> . ?r bsml:eventType <%s>'
                                  % (rec_uri, eventtype))
    if timetype is not None:
      condition += ' . ?r bsml:time ?tm . ?tm a <%s>' % timetype
    return [ r[1]
      for r in self.get_resources(BSML.Event, rvars='?r', condition=condition,
        prefixes=dict(bsml=BSML.prefix), graph=graph_uri)
      ]

  ### Add a get_events() similar to get_annotations(), ideally be using
  ### a generic method -- get_resources(cls, ...) ???


  def event_types(self, rec_uri, counts=False, graph_uri=None):
  #------------------------------------------------------------
    '''
    Return a list of all types of Events associated with a recording.

    :param uri: The URI of the recording.
    :param counts: Optionally return a count of each type of event.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: list of bsml:Event URIs if no counts, otherwise tuple(URI, count).
    '''
    return [ tuple(r[1:3]) if counts else r[1]
      for r in self.get_resources(BSML.Event, rvars='?et count(?et) as ?count',
        condition = '?e bsml:recording <%s> . ?e bsml:eventType ?et' % rec_uri,
        group = '?et',
        prefixes = dict(bsml=BSML.prefix),
        graph = graph_uri, resource='?e'
        ) ]


  def get_annotation(self, uri, graph_uri=None):
  #---------------------------------------------
    '''
    Get an Annotation from the repository.

    :param uri: The URI of an Annotation.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Annotation`
    '''
    # The following line works around a Virtuoso problem
    if graph_uri is None: graph_uri = self.get_graph_and_recording_uri(uri)[0]
    graph = self.get_resource_as_graph(uri, BSML.Annotation, graph_uri)

##### Put into Annotation/Segment.load_from_graph()   ????
    for sg in graph.get_objects(uri, DCT.subject):  ## This could be improved...
      graph.append_graph(self.get_resource_as_graph(sg.uri, BSML.Segment, graph_uri))
      for tm in graph.get_objects(sg.uri, BSML.time):  ## This could be improved...
        graph.append_graph(self.get_resource_as_graph(tm.uri, BSML.Instant, graph_uri))
        graph.append_graph(self.get_resource_as_graph(tm.uri, BSML.Interval, graph_uri))

    return Annotation.create_from_graph(uri, graph)

  def get_annotation_uris(self, subject, graph_uri=None):
  #------------------------------------------------------
    """
    Return all Annotation URIs about a subject.

    :param subject: The URI of the subject.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: list of bsml:Annotation URIs
    """
    return [ r[1]
      for r in self.get_resources(BSML.Annotation, rvars='?ann',
        condition='''?ann a bsml:Annotation ;
                          dct:subject <%(subj)s>
                            minus { [] prv:precededBy ?ann }
                   } union {
                     ?ann a bsml:Annotation ;
                          dct:subject [ a bsml:Segment ;
                                        dct:source <%(subj)s>
                                      ]
                            minus { [] prv:precededBy ?ann }'''
                   % dict(subj=subject),
## Following produces an internal Virtuoso error...
#                    {
#                      { ?ann dct:subject <%(subj)s> }
#                     union
#                      { ?ann dct:subject [ a bsml:Segment ; dct:source <%(subj)s> ] }
#                    }
#                  minus { [] prv:precededBy ?ann }
        prefixes = dict(bsml=BSML.prefix, dct=DCT.prefix, prv=PRV.prefix),
        graph = graph_uri
        ) ]

  def get_annotations(self, subject, graph_uri=None):
  #--------------------------------------------------
    """
    Return all Annotations about a subject.

    This is significantly faster (approx 15x) then getting a list of URIs
    (fast) and then creating Annotations (slow).

    Code could be used as a template for general abstract object creation
    based on PropertyMap and bypassing internal use of RDF -- instead map
    directly to and from SPARQL.

    :param subject: The URI of the subject.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: list of bsml:Annotations
    """
    anns = self.get_resources(BSML.Annotation,
        rvars='?ann ?about ?stype ?comment ?tag ?created ?source ?tm ?start ?duration ?timeline',
        condition='''minus { [] prv:precededBy ?ann }
                       {
                         ?ann dct:subject ?about .
                         ?about a ?stype .
                         optional { ?ann rdfs:comment ?comment }
                         optional { ?ann dct:created ?created }
                         optional { ?ann bsml:tag ?tag }
                         { ?ann dct:subject <%(subject)s> }
                         union
                         { ?about a bsml:Segment ;
                             dct:source <%(subject)s> ;
                             dct:source ?source ;
                             bsml:time ?tm .
                             ?tm tl:timeline ?timeline .
                           { ?tm a bsml:Interval ; tl:start ?start ; tl:duration ?duration }
                           union
                           { ?tm a bsml:Instant ; tl:at ?start }
                         }
                       }''' % dict(subject=subject),
        prefixes = dict(bsml=BSML.prefix, dct=DCT.prefix, prv=PRV.prefix, tl=TL.prefix),
        graph = graph_uri,
#       order = '?start',  ## Virtuoso doesn't correctly sort xsd:dayTimeDuration
        )
    anns.sort(key=operator.itemgetter(9, 2, 1))  # start, about, uri
    annotations = [ ]
    for a in anns:
      ann = Annotation(a[1], about=a[2], comment=a[4], created=a[6])
      if str(a[3]) == str(BSML.Segment):
        time = TemporalEntity.create(a[8], float(a[9]),
          duration=None if a[10] in ['', None] else float(a[10]),
          timeline=a[11])
        ann.about = Segment(a[2], source=a[7], time=time)
      annotations.append(ann)
    return annotations

  def get_semantic_tags(self):
  #---------------------------
    """
    Get all labelled semantic tags stored in the repository's SEMANTIC_TAGS graph.

    :return: Dictionary of { uri: label }.
    """
    return { str(sparqlstore.get_result_value(r, 'uri')):
                   sparqlstore.get_result_value(r, 'label')
               for r in self.select('?uri ?label',
                                    '?uri a bsml:SemanticTag . ?uri rdfs:label ?label',
                                    prefixes=dict(bsml=BSML.prefix, rdfs=RDFS.prefix),
                                    graph=SEMANTIC_TAGS) }


class BSMLUpdateStore(BSMLStore, GraphUpdate):
#=============================================

  def extend_recording_graph(self, recording, *abstractobjects):
  #-------------------------------------------------------------
    """
    Add abstractobjects to a recording's graph.
    """
    for abstractobject in abstractobjects:
      self._sparqlstore.extend_graph(recording.graph.uri,
        abstractobject.metadata_as_string(format=Format.RDFXML),
        format=Format.RDFXML)

  def remove_recording_resource(self, recording, uri):
  #---------------------------------------------------
    """
    'Remove' a resource from a recording's graph.

    This is done by asserting the resource precedes `bsml:deletedResource`,
    so provenance aware queries will then return an empty result set.
    """
    self._sparqlstore.insert_triples(recording.graph.uri,
      [("bsml:deletedResource", "prv:precededBy", "<%s>" % uri)],
      prefixes=dict(bsml=BSML.prefix, prv=PRV.prefix))

  def add_recording_graph(self, uri, graph_rdf, creator, format=Format.RDFXML):
  #---------------------------------------------------------------------------
    """
    Add RDF metadata describing a recording as a new named graph.

    Provenance statements will be made about the new graph, including
    linking it to any previous graph describing the recording.
    """
    return self.add_resource_graph(uri, BSML.Recording, graph_rdf, creator, format=format)

  def store_recording(self, recording, creator=None):
  #--------------------------------------------------
    """
    Store a recording's metadata in the repository.

    :param recording: The :class:`~biosignalml.Recording` to store.
    :param creator: Who or what is storing the recording.
    """
    return self.add_recording_graph(recording.uri,
      recording.metadata_as_graph().serialise(Format.RDFXML), creator, Format.RDFXML)
