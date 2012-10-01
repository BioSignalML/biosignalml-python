######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
######################################################

import logging

from tornado.options import options

import biosignalml.formats

from biosignalml import BSML, Recording, Signal, Event, Annotation
from biosignalml.utils import xmlescape

from biosignalml.rdf import DCTERMS
from biosignalml.rdf import Format

from repository import Repository


class BSMLRepository(Repository):
#================================
  '''
  An RDF repository containing BioSignalML metadata.
  '''

  def has_recording(self, uri):
  #----------------------------
    ''' Check a URI refers to a Recording. '''
    return self.has_current_resource(uri, BSML.Recording)

  def has_signal(self, uri):
  #-------------------------
    ''' Check a URI refers to a Signal. '''
    return self.has_current_resource(uri, BSML.Signal)

  def has_signal_in_recording(self, sig, rec):
  #-------------------------------------------
    ''' Check a URI refers to a Signal in a given Recording. '''
    return (self.has_current_resource(rec, BSML.Recording)
        and self.has_current_resource(uri, BSML.Signal))

  def recordings(self):
  #--------------------
    """
    Return a list of URI's of the Recordings in the repository.

    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    """
    return self.get_current_resources(BSML.Recording)

  def get_recording_and_graph_uri(self, uri):
  #------------------------------------------
    """
    Get the URIs of the recording and its Graph that contain the object.

    :param uri: The URI of some object.
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    return self.get_current_resource_and_graph(uri, BSML.Recording)

  def get_recording(self, uri):
  #----------------------------
    '''
    Get the Recording from the graph that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    '''
    #logging.debug('Getting: %s', uri)
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    #logging.debug('Graph: %s', graph_uri)
    if graph_uri is not None:
      rclass = biosignalml.formats.CLASSES.get(
                 str(self.get_objects(rec_uri, DCTERMS.format, graph=graph_uri))[0],
                 Recording)
      graph = self.make_graph(graph_uri, '?s ?p ?o', graph=graph_uri)
      return rclass.create_from_graph(rec_uri, graph, signals=False)
    else:
      return None

  def get_recording_with_signals(self, uri):
  #-----------------------------------------
    """
    Get the Recording with its Signals from the graph
      that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    """
    rec = self.get_recording(uri)
    if rec is not None:
      for r in rec.graph.query("select ?s where { ?s a <%s> . ?s <%s> <%s> } order by ?s"
                               % (BSML.Signal, BSML.recording, rec.uri)):
        rec.add_signal(rec.SignalClass.create_from_graph(str(r['s']), rec.graph, units=None))
    return rec

  def store_recording(self, recording):
  #------------------------------------
    """
    Store a recording's metadata in the repository.

    :param recording: The :class:`~biosignalml.Recording` to store.
    """
    self.replace_graph(recording.uri, recording.metadata_as_graph().serialise())


#  def signal_recording(self, uri):
#  #-------------------------------
#    return self.get_object(uri, BSML.recording)

  def get_signal(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get a Signal from the repository.

    :param uri: The URI of a Signal.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Signal`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a  bsml:Signal . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.NS.prefix),
                            graph = graph_uri
                            )
    return Signal.create_from_graph(uri, graph, units=None)  # units set from graph...

#  def signal(self, sig, properties):              # In context of signal's recording...
#  #---------------------------------
#    if self.check_type(sig, BSML.Signal):
#      r = [ [ Graph.make_literal(t, '') for t in self.get_objects(sig, p) ] for p in properties ]
#      r.sort()
#      return r
#    else: return None


  def get_event(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get an Event from the repository.

    :param uri: The URI of an Eventt.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Event`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a  bsml:Event . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.prefix),
                            graph = graph_uri
                            )
    return Event.create_from_graph(uri, graph, eventtype=None)  # eventtype set from graph...

  def get_annotation(self, uri, graph_uri=None):
  #---------------------------------------------
    '''
    Get an Annotation from the repository.

    :param uri: The URI of an Annotation.
    :rtype: :class:`~biosignalml.Annotation`
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    if graph_uri is None: return None
    graph = self.make_graph(uri, '<%(uri)s> ?p ?o',
                            where = '<%(uri)s> a bsml:Annotation . <%(uri)s> ?p ?o',
                            params = dict(uri=uri),
                            prefixes = dict(bsml=BSML.prefix),
                            graph = graph_uri
                            )
    return Annotation.create_from_graph(uri, graph)

#  def get_annotation_by_content(self, uri, graph_uri=None):
#  #--------------------------------------------------------
#    '''
#    Get an Annotation from the repository identified by its body content.
#
#    :param uri: The URI of the body of an Annotation.
#    :rtype: :class:`~biosignalml.Annotation`
#    '''
#    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
#    for r in self._triplestore.select('?a', 'graph <%(g)s> { ?a a oa:Annotation . ?a oa:hasBody <%(u)s> }',
#                                      params = dict(g=graph_uri, u=uri),
#                                      prefixes = dict(oa = OA.prefix),
#                                      ):
#      return self.get_annotation(r['a']['value'], graph_uri)

  def annotations(self, uri, graph_uri=None):
  #------------------------------------------
    '''
    Return a list of all Annotations about a subject.

    :param uri: The URI of the subject.
    :rtype: list of URIs to oa:Annotations
    '''
    if graph_uri is None: rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    return [ (r['a']['value'])
      for r in self._triplestore.select('?a',
        '?a a bsml:Annotation . ?a bsml:about <%s> . optional { ?a dct:created ?tm }' % uri,
        graph = graph_uri,
        prefixes = dict(bsml=BSML.prefix, dct=DCTERMS.prefix),
        order = '?a ?tm') ]
