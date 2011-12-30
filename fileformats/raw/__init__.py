######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


from biosignalml.bsml import BSML
from biosignalml.utils import file_uri

from biosignalml.fileformats import BSMLRecording


class RAWRecording(BSMLRecording):
#==================================

  def __init__(self, fname, uri=None, metadata=None):
  #-------------------------------------------------

    self._file = open(fname, 'rb')

    if metadata is None: metadata = { }
    metadata['format'] = BSML.RAW
    metadata['source'] = file_uri(fname)

    super(RAWRecording, self).__init__(uri=uri, metadata = metadata)


  def close(self):
  #---------------
    self._file.close()
