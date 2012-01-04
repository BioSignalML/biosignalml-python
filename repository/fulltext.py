import apsw
import logging

from biosignalml.metadata import rdf
from biosignalml.bsml import BSML


_db = None

def _execute(sql, *args):
#========================
  cursor = _db.cursor()
  return cursor.execute(sql, *args)


RDF_TYPE_URI = 0

def _uricode(uri):
#=================
  for r in _execute('select id from uris where uri = ? limit 1', (uri,)):
    return int(r[0])
  return 0


def initialise(options):
#=======================
  global _db, RDF_TYPE_URI
  if options['store'] != 'sqlite':
    raise Exception('Full text search only implemented for SQLite') 
  _db = apsw.Connection(options['database'])

  RDF_TYPE_URI = _uricode(str(rdf.type))

  #
  #select id from uris where uri in (
  #  ## comment...
  #  'http://purl.org/dc/terms/description',
  #  'http://www.w3.org/2000/01/rdf-schema#label')
  # order by uri ;


BOLD_ON  = '{{BOLD}}'
BOLD_OFF = '{{bold}}'
ELLIPSES = BOLD_ON + '...' + BOLD_OFF

def search(text):
#================

  sql = """select c.uri, s.uri, p.uri, snippet(fulltext, '%s', '%s', '%s')
             from fulltext as ft
               left join triples as t on ft.docid = t.objectLiteral
               left join triples as cl on t.subjectUri = cl.subjectUri and cl.predicateUri = %d
               left join uris as c on c.id = cl.objectUri
               left join uris as s on s.id = t.subjectUri
               left join uris as p on p.id = t.predicateUri
           where ft.text match ?
           order by c.uri, s.uri, p.uri""" % (
            BOLD_ON, BOLD_OFF, ELLIPSES,
            RDF_TYPE_URI,
            )
#  and cl.predicateUri = %d and cl.objectUri in (%d, %d)
#  _uricodes[BSML_RECORDING_URI], _uricodes[BSML_SIGNAL_URI],

  logging.debug('FIND: %s', text)

  return _execute(sql, (text,))
  #for r in _execute(sql, (text,)):
  #  logging.debug('ROW: %s', r)
  #return [ ]

  """

  SPARQL fulltext search proposals -- see http://www.w3.org/2009/sparql/wiki/Feature:FullText

  What to return:

    <subject, predicate, text_snippet>

    context??

    rdf:type of subject ??  (as a URI string??)

    Map predicate URIs to text for rdfs:label etc?? But we may have localised
    prompts for common predicates.


  What about find uris.id of bsml:Recording, bsml:Signal, bsml:Event and bsml:Annotation

  and def find_recordings(text) then filters s.id with

    s.id rdf:type bsml:Recording

    left join triples as c on t.subjectUri = c.subjectUri and c.predicateUri = RDF_TYPE_URI
     and c.objectUri = BSML_RECORDING_URI

  Do we provide helper functions to directly find rdf:type etc? Or use metadata
  properties? Redland calls? And what about context?? 


  What about a 'repo:' namespace?? Set to options.repository['import_base'] ??
  Or use this as a base, so signals and recordings have form ':sinewave/1' etc??


  What are the "things" that BSML is about?

    * Signals
    * Recordings
    * Events
    * Annotations
    * Time (incl. TimeLines)


  And metadata values used to describe the "things" (= data to be searched)?

    * type of event (domain specific, loaded from an ontology)
    * Label text
    * Descriptions
    * Comments
    * Annotation text
    * Time of events (Instants, Intervals (start, end, duration))


  Along with predicates (properties) that relate a "thing" to its metadata values:


  Search terms and their relationships:

    * Text relationships (match, starts with, contains, ...)
    * Temporal relationships (Allen's paper, before, at, after, overlaps, included, etc...)
    * Boolean logic (and, or, not)


  """
