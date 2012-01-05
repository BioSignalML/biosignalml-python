######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


from biosignalml.model       import BSML
from biosignalml.fileformats import BSMLRecording
from biosignalml.utils       import file_uri


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
