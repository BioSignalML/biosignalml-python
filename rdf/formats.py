######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: a20277b on Thu Jul 7 16:40:26 2011 +1200 by Dave Brooks $
#
######################################################


class Format(object):
#====================
  '''Different RDF representation formats.'''
  RDFXML = 'rdfxml'
  TURTLE = 'turtle'
  JSON   = 'json'

  mimetypes = { RDFXML: 'application/rdf+xml',
                TURTLE: 'text/turtle',
                JSON:   'application/json',
              }

  @staticmethod
  def mimetype(format):
  #--------------------
    '''
    Get the MIME type of a RDF representation.

    :param format: A RDF representation.
    :rtype: str
    '''
    return Format.mimetypes[format]
