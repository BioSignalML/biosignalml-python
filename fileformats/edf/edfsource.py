######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: edfsource.py,v 284857bd6a99 2011/02/11 00:51:33 dave $
#
######################################################


import urllib
import logging

from biosignalml.model.data import TimeSeries
from edffile import EDFFile


class EDFSource(object):
#======================

  def __init__(self, fileuri, signals, intervals=None, rawmode=False):
  #-------------------------------------------------------------------
    self._edf = None
    try:
      self._edf = EDFFile.uriopen(fileuri)
      if self._edf.errors:      ### Repository should only have good files...
        logging.error("EDF file '%s' has errors",fileuri)
        raise Exception("'%s' EDF file has errors..." %fileuri)
    except Exception, msg:      ### File should be available...
      logging.error("%s: Cannot open EDF file '%s'", msg, fileuri)
      raise Exception("%s: Cannot open EDF file '%s'..." % (msg, fileuri))
    self._siguris = [ s.uri         for s in signals ]
    self._signums = [ int(s.id) - 1 for s in signals ]
    self._rawmode = rawmode
    self._intervals = intervals if intervals else [ None ]

  def __del__(self):
  #----------------
    if self._edf: self._edf.close()

  def frames(self):
  #---------------
    for interval in self._intervals:
      if self._rawmode:
        for record in self._edf.raw_records(self._signums, interval):
          for n, sigdata in enumerate(record[0]):
            yield TimeSeries(self_siguris[n], *sigdata, scaling=self._edf.scaling[sigdata[0]])
      else:
        for record in self._edf.physical_records(self._signums, interval):
          for n, sigdata in enumerate(record[0]):
            yield TimeSeries(self._siguris[n], *sigdata)
