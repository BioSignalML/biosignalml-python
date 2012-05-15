######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: 60c35bd on Tue May 1 11:33:00 2012 +1200 by Dave Brooks $
#
######################################################


from biosignalml         import BSML
from biosignalml.formats import BSMLRecording
from biosignalml.utils   import file_uri


class RAWRecording(BSMLRecording):
#==================================

  FORMAT = BSML.RAW
  MIMETYPE = 'application/x-raw'

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
