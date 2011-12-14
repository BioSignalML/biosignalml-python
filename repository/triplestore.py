######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: a20277b on Thu Jul 7 16:40:26 2011 +1200 by Dave Brooks $
#
######################################################


class TripleStore(object):
#=========================

  def __init__(self, href):
  #------------------------
    self._href = href

  def query(self, sparql, accept='application/xml'):
  #-------------------------------------------------
    pass

  def ask(self, where):
  #--------------------
    pass

  def select(self, fields, where, distinct=False, limit=None):
  #-----------------------------------------------------------
    pass

  def construct(self, graph, where, params = { }, format='text/turtle'):
  #---------------------------------------------------------------------
    pass

  def describe(self, uri, format='application/xml'):
  #-------------------------------------------------
    pass

  def insert(self, graph, triples):
  #--------------------------------
    pass

  def extend_graph(self, graph, turtle):
  #-------------------------------------
    pass

  def replace_graph(self, graph, rdf, format='application/x-turtle'):
  #------------------------------------------------------------------
    pass

  def delete_graph(self, graph):
  #-----------------------------
    pass
