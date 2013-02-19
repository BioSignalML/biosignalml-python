######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2013  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
######################################################

from biosignalml         import BSML
from biosignalml.formats import BSMLRecording
from biosignalml.utils   import file_uri


class RAWRecording(BSMLRecording):
#==================================

  MIMETYPE = 'application/x-bsml+raw'

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
