#===============================================================================

import biosignalml.rdf as rdf
from biosignalml.model import Recording

#===============================================================================

if __name__ == '__main__':
#=========================

  uri = 'http://ex.org/test'
  rdftext = """@prefix dct: <http://purl.org/dc/terms/> .
@prefix bsml: <http://www.biosignalml.org/ontologies/2011/04/biosignalml#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<%s>
 	dct:extent "PT1S"^^xsd:dayTimeDuration ;
 	a bsml:Recording ;
 	rdfs:label "noble 1962" .""" % uri

  graph = rdf.Graph.create_from_string(uri, rdftext, format=rdf.Format.TURTLE)

  rec = Recording.create_from_graph(uri, graph, signals=False)

  print rec.duration

#===============================================================================
