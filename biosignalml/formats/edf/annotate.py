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

import math
import copy

from biosignalml.formats.edf import EDF, EDFFile

__all__ = [ 'Annotation', 'annotate' ]


class Annotation(object):
#=======================
  """
  An annotation to add to an EDF+ file.

  :param text (str): The annotation text.
  :param float start: The start time of the annotation in seconds.
  :param float duration: The length of the annotation. in seconds.

  """

  def __init__(self, text, start, duration=0):
  #-------------------------------------------
    self._text = text
    self._start = start
    self._duration = duration
  
  def make_TAL(self):
  #------------------   
    tal = [ ]
    if self._start >= 0: tal.append('+')
    tal.append(str(self._start))
    if self._duration:
      tal.append('\x15')
      tal.append(str(self._duration))
    tal.append('\x14')
    tal.append(self._text)
    tal.append('\x14\x00')
    return ''.join(tal)


# Month name abbreviations have to be in English and uppercase for EDF+
_months = { 1: 'JAN', 2: 'FEB', 3: 'MAR',  4: 'APR',  5: 'MAY',  6: 'JUN',
            7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC' }


def annotate(source, outfile, annotations):
#==========================================
  """
  Add annotations to an EDF(+) file, creating a new file.
  
  The existing file is copied as EDF+ before an `EDF Annotations` signal
  is added to it.

  :param str source: The name of an EDF file.
  :param str outfile: The name of the EDF+ file to create.
  :param list annotations: A list of :class:`Annotation`.

  """

  input = EDFFile.open(source)
  if input.errors: input.fixheader()

  output = copy.deepcopy(input)
  output._file = open(outfile, 'wb+')

  if input.edf_type == EDF.EDF:
    output.edf_type = EDF.EDFplusC
    output.patient_code = input.patient
    output.recording_date = '%02d-%s-%04d' % (input.start_datetime.day,
                                           _months[input.start_datetime.month],
                                           input.start_datetime.year)
    output.recording_code = input.recording

    # We insist digmax > digmin in header checks, otherwise we could...
    # check digmax > digmin and if < then swap physmax/min

    ##  Minimum EDF Annotation has block start times
    # Find longest length of record start timestamp
    tlen = len(str(int(input.duration))) + len(str(input._drduration - int(input._drduration)))
    tlen += 3        # Allow for marker bytes
  else:
    tlen = 0         # EDF+ will already have record timstamps

  # First sort into time order...
  annotations.sort(key = lambda a: a._start)

  # Then group so len(groups) <= input._datarecs
  groupcount = int(math.ceil(float(len(annotations))/input._datarecs))

  maxlen = 0
  groups = [ ]
  group = [ ]
  n = 0
  for ann in annotations:
    if n == groupcount:
      groups.append(''.join(group))
      grouplen = len(groups[-1])  # Length of group just added
      if grouplen > maxlen: maxlen = grouplen
      grouplen = 0
      group = [ ]
      n = 0
    group.append(ann.make_TAL())
    n += 1
  groups.append(''.join(group))
  grouplen = len(groups[-1])
  if grouplen > maxlen: maxlen = grouplen

  annsize = maxlen + tlen
  if annsize:
    annsig = output._add_annotation_signal(annsize)
    annsize = 2*output.nsamples[annsig]

  output.writeheader()
  for n in xrange(0, input._datarecs):
    output._file.write(input._file.read(input._recsize))
    if annsize:
      timekeep = ('+%s\x14\x14\00' % str(n * input._drduration)) if tlen else ''
      tals = groups[n] if n < len(groups) else ''
      output._file.write((timekeep + tals).ljust(annsize, '\x00'))
  output.close()
  input.close()



if __name__ == '__main__':
#=========================

  import os, sys
  from optparse import OptionParser

  def getarguments():
  #=================
    global options
    parser = OptionParser(usage='usage: %prog [options] input_file output_file',
                          description='Create an EDF+ file, copying the input records'
                                     + ' and optionally adding annotations.')
    parser.add_option("-a", "--annotate", dest="annfile",
                      help="a file containing annotations", metavar="FILE")
    (options, args) = parser.parse_args()
    if len(args) < 2: parser.error('missing input and output file names')
    return args



  args = getarguments()

  infile = args[0]
  outfile = args[1]
  if not os.path.exists(infile):
    print "Missing file '%s'" % infile
    sys.exit()



  annotations = [ Annotation('Test 1.5', 1.5, 0.2),
                  Annotation('Test 1.8', 1.8, 0.1),
                  Annotation('Test 0.5', 0.5, 0.2),
                  Annotation('Test 0.1', 0.1, 0.1),
                  Annotation('Test 4.5 instant', 4.5),
                ]
  annotate(infile, outfile, annotations)

