######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: config.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import ConfigParser, os


OPTIONS_FILE = 'biosignalml.ini'


def getOptions(section, file=OPTIONS_FILE, defaults=None):
#========================================================
  data = defaults
  cfg = ConfigParser.SafeConfigParser(defaults)
  cfg.optionxform = str   # Preserve case (default method translates to lowercase)
  try:
    cfg.read(file)
    data = dict(cfg.items(section))
  except IOError:
    pass
  except ConfigParser.NoSectionError:
    pass
  return data


class Options(object):
#====================

  def __init__(self, file=OPTIONS_FILE, defaults = { } ):
  #-----------------------------------------------------
    cfg = ConfigParser.SafeConfigParser()
    cfg.optionxform = str   # Preserve case (default method translates to lowercase)
    cfg.read(file)
    for s in cfg.sections(): setattr(self, s, dict(cfg.items(s, defaults.get(s, None))) )



if __name__ == '__main__':
#=========================

  print getOptions('triplestore')
