######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $Id$
#
######################################################


from datetime import datetime

from biosignalml.rdf import Graph, Statement
from biosignalml.rdf import DCTERMS


class Provenance(Graph):
#=======================

  def __init__(self, store, uri):
  #-------------------------
    super(Provenance, self).__init__(uri)
    self.__store = store

  def add(self, uri): ## , format, digest):
  #------------------------------------
    self.append(Statement(uri, DCTERMS.dateSubmitted, datetime.utcnow().isoformat()))
    ##### self.append(Statement(uri, DCTERMS.format,        format))
    ## And need to now put these into the store....

  def delete(self, graph):
  #---------------------
    ## 'DCTERMS.dateRemoved' is not a DCTERMS Terms property...
    self.append(Statement(uri, DCTERMS.dateRemoved, datetime.utcnow().isoformat()), self)
    ## ANd need to updayte the store...


#    def transaction(self, resource, action, comment):
    #------------------------------------------------

    #self._store.insert(self, triples...)

## Also store md5/sha hashes of file objects...


"""

Access everything via <provenance> graph:


<rec_uri> a bsml:Recording ;
          prov:hasGraphs <rec_graph/1>, <rec_graph/2>, <rec_graph/3> ;
          prov:currentGraph <rec_graph/3> ;
          .

<rec_graph/1> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              dc:replacedBy <rec_graph/2> 
              prov:version 1 ;
              prov:validFrom "..."^^xsd:DateTime ;
              prov:validUntil "..."^^xsd:DateTime ;
              .

<rec_graph/3> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              dc:replaceds <rec_graph/2> 
              prov:version 3 ;
              prov:validFrom "..."^^xsd:DateTime ;
              .


<del_uri> a bsml:Recording ;
          prov:hasNamedGraphs <del_graph/1> ;
          .
          .

<del_graph/1> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              prov:version 1 ;
              prov:validFrom "..."^^xsd:DateTime ;
              prov:validUntil "..."^^xsd:DateTime ;
              .

"""



## Instead keep transactions:
"""
:transactionN
  a prov:Transaction ;
  dcterms:created "date-time" ;  now
  dcterms:creator ... ;          user/machine/  mark@www
  dcterms:source  <uri> ;        resource
  rdfs:comment "..." ;
  prov:action prov:Added ;   action

These should be about the graph...
  dcterms:versionOf
  dcterms:replaces/modifies
  dcterms:hasVersion

This should be in the graph, pointing to provenance statement.
  dcterms:provenance


  .


<graph_uri> dcterms:replaces <prev_graph_uri>



select ?what ?who ?when ?format from <provenence-graph> where {
  ?t dcterms:source <uri> .
  ?t a prov:Transaction .
  ?t prov:action ?what .
  ?t dcterms:created ?when .
  ?t dcterms:creator ?who .
  } order by ?when
"""


"""

Provenance is like Recording -- both are Metadata objects with a NamedGraph??


Abstract v's concrete (realisation, representation)

Native (or natural ??) programmatic interface to a signal file.
along with a mapping to ontological terms.




<hhj>
  a bsml:Recording ;
  dcterms:provenance
  bsml:added [ a dcterms:ProvenanceStement ;
               dcterms:created "2011-03-07T15:38" ;
               dcterms:creator "dave@djbmac" ;
               rdfs:comment "imported to repo..."
              ] .

"""
