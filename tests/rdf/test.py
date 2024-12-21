from rdflib.term import URIRef

from __init__ import *


ttl="""
@prefix ns2: <http://purl.org/dc/terms/> .
@prefix ns3: <http://www.biosignalml.org/ontologies/2011/04/biosignalml#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://devel.biosignalml.org/opencor/Users/dave/build/opencor/gall.h5> rdf:type ns3:Recording ;
    ns2:description "Something describing the recording." ;
    ns2:format "application/x-bsml+hdf5" ;
    ns3:dataset <file:///Users/dave/build/opencor/gall.h5> .
"""

g = Graph.create_from_string("g", ttl, format=Format.TURTLE)

s1 = (URIRef('http://devel.biosignalml.org/opencor/Users/dave/build/opencor/gall.h5'),
      URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
      URIRef('http://www.biosignalml.org/ontologies/2011/04/biosignalml#Recording')
     )

s2 = (Resource('http://devel.biosignalml.org/opencor/Users/dave/build/opencor/gall.h5'),
      Resource('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
      Resource('http://www.biosignalml.org/ontologies/2011/04/biosignalml#Recording')
     )


def pr(g):
  print(g.serialize(format='turtle'))
