######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID: c9e447e on Wed Mar 3 12:53:44 2010 +1300 by dave $
#
######################################################


import sys
from biosignalml.rdfmodel import NS

"""
# Directly use classes from RDF package
NS        = RDF.NS
Uri       = RDF.Uri
Node      = RDF.Node
Statement = RDF.Statement
"""

# Define generic namespaces:
NAMESPACES = {
  'xsd':  'http://www.w3.org/2001/XMLSchema#',
  'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
  'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
  'owl':  'http://www.w3.org/2002/07/owl#',
  'dcterms': 'http://purl.org/dc/terms/',
  'evt':  'http://purl.org/NET/c4dm/event.owl#',
  'tl':   'http://purl.org/NET/c4dm/timeline.owl#',
  }
for prefix, name in NAMESPACES.iteritems():
  setattr(sys.modules[__name__], prefix.upper(), NS(name))

"""
# Make our classes available at package level:
from model import Model, make_literal
from graph import Graph


class Resource(RDF.Node):
#========================

  def extend_uri(self, suffix):
  #---------------------------
    return Uri(str(self.uri) + suffix)


class BlankNode(RDF.Node):
#=========================
  pass


class Literal(RDF.Node):
#=======================

  def __init__(self, string, **kwds):
  #----------------------------------
    RDF.Node.__init__(self, literal=string, **kwds)
"""
