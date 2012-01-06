######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: a20277b on Thu Jul 7 16:40:26 2011 +1200 by Dave Brooks $
#
######################################################


from formats import Format


class TripleStore(object):
#=========================

  def __init__(self, href):
  #------------------------
    self._href = href

  def query(self, sparql, format=Format.RDFXML):
  #---------------------------------------------
    pass

  def ask(self, where):
  #--------------------
    pass

  def select(self, fields, where, distinct=False, limit=None):
  #-----------------------------------------------------------
    pass

  def construct(self, graph, where, params = { }, format=Format.RDFXML):
  #---------------------------------------------------------------------
    pass

  def describe(self, uri, format=Format.RDFXML):
  #-----------------------------------------------
    pass

  def insert(self, graph, triples):
  #--------------------------------
    pass

  def extend_graph(self, graph, rdfdata, format=Format.RDFXML):
  #------------------------------------------------------------
    pass

  def replace_graph(self, graph, rdf, format=Format.RDFXML):
  #---------------------------------------------------------
    pass

  def delete_graph(self, graph):
  #-----------------------------
    pass
