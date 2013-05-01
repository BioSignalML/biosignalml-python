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

import os
import re
import math
import numpy as np
import urllib
import logging
from datetime import datetime
from collections import namedtuple

__all__ = [ 'EDFFile', 'FormatError', 'InvalidSignalId' ]


class FormatError(Exception):
  pass

class InvalidSignalId(Exception):
  pass


nonprinting = re.compile(r'[^ -~]')

options = { }

FILEHDR   = [ ('version',      8, str),
              ('patient',     80, str),
              ('recording',   80, str),
              ('startdate',    8, str),    # DD.MM.YY (year = 84 => 2084; 85 => 1985)
              ('starttime',    8, str),    # HH.MM.SS
              ('_hdrsize',     8, int),
              ('_reserved',   44, str),
              ('_datarecs',    8, int),
              ('_drduration',  8, float),
              ('_nsignals',    4, int),
            ]

SIGNALHDR = [ ('label',       16, str),
              ('transducer',  80, str),
              ('units',        8, str),
              ('_physmin',     8, float),
              ('_physmax',     8, float),
              ('_digmin',      8, int),
              ('_digmax',      8, int),
              ('prefilter',   80, str),
              ('nsamples',     8, int),
              ('_reservedS',  32, str),
            ]

PATIENTFIELDS = [ 'patient_code',
                  'patient_gender',
                  'patient_birthdate',
                  'patient_name',
                ]

RECORDINGFIELDS = [ 'recording_date',
                    'recording_code',
                    'recording_investigator',
                    'recording_equipment',
                  ]


RecordData = namedtuple('RecordData', 'channel, starttime, rate, data')
'''A tuple containg data from an EDF record.'''

SignalData = namedtuple('SignalData', 'startpos, length, data')
'''A tuple containg data for a signal.'''

Scaling = namedtuple('Scaling', 'scale, offset')
'''A tuple for scaling.'''


class EDF(object):
#=================
  """ Types of EDF/EDF+ file.

  """
  EDF      = 1      # EDF
  EDFplusC = 2      # EDF+, contiguous data records
  EDFplusD = 3      # EDF+, discontinuous data records


class TimeStampedAnnotation(object):
#===================================

  def __init__(self, TALdata):
  #---------------------------
    # <offset><duration>0x14<annotationlist>0x00
    #  <offset> ::- (+|-)<digits>[.<digits>]
    #  <duration> ::= <empty> || 0x15<digits>[.<digits>]
    #  <annotationlist> ::= <annotation><annotationlist>
    #  <annotation> := <unicode text>0x14
###    print "TAL: %s", str(['%02x' % ord(d) for d in TALdata])
    if TALdata[-1] != '\x14': raise FormatError("Unterminated TAL record")
    fields = TALdata.rstrip('\x14').split('\x14')
    times = fields[0].split('\x15')
    if len(times) > 2: raise FormatError("Invalid TAL time header")
    self.onset = float(times[0])
    if len(times) > 1: self.duration = float(times[1])
    else:              self.duration = 0
    self.annotations = [ a.strip() for a in fields[1:] ]

  def __str__(self):
  #-----------------
    return "[%f:%f]: %s" % (self.onset, self.duration, str(self.annotations))


class EDFFile(object):
#=====================

  def __init__(self):
  #------------------
    self._file = None
    self._newfile = False
    self.errors = [ ]
    for (f, l , t) in FILEHDR:
      setattr(self, f, '' if t == str else 0.0 if t == float else 0)
    for (f, l, t) in SIGNALHDR: setattr(self, f, [])
    for f in PATIENTFIELDS: setattr(self, f, '')
    for f in RECORDINGFIELDS: setattr(self, f, '')
    self._hdrsize = 256

  def __del__(self):
  #-----------------
    self.close()

  @classmethod
  def open(cls, fname):
  #--------------------
    try:
      self = cls()
      self._open(urllib.urlopen(fname).fp)
      return self
    except Exception:
      return None

  @classmethod
  def fp_open(cls, fp):
  #--------------------
    self = cls()
    self._open(fp)
    return self

  @classmethod
  def create(cls, fname):
  #----------------------
    self = cls()
    self._create(open(fname, 'wb'))
    return self

  def close(self):
  #---------------
    if self._file != None:
      if self._newfile:
        if self._recbuffers.in_use(): raise Exception("Last EDF record is incomplete")
        self._datarecs = self._recbuffers._recordno 
        self.duration = self._datarecs*self._drduration
        self.writeheader()       ## Update datarecs field
      self._file.close()
      self._file = None

  def _create(self, filep):
  #-----------------------
    self._file = filep
    self._newfile = True
       
  def _open(self, filep):
  #---------------------
    self._file = filep
    self._getfields('file header', self._file.read(256), FILEHDR)
    self._getfields('signal headers', self._file.read(256*self._nsignals), SIGNALHDR, self._nsignals)
    if self._hdrsize != 256*(self._nsignals + 1):
      self._error('Header size mismatch -- expected %d, have %d bytes'
                  % (self._hdrsize, 256*(self._nsignals + 1)))
    self.start_datetime = datetime.strptime(self.startdate + self.starttime, '%d.%m.%y%H.%M.%S')
    if self.start_datetime.year < 1985:       # EDF century start is 1985
      self.start_datetime = self.start_datetime.replace(self.start_datetime.year + 100)

    #: Indices to EDF+ annotations.
    self.annotation_signals = [ i for i in xrange(0, self._nsignals)
                                  if self.label[i] == 'EDF Annotations' ]
    
    #: A list of indices to data signals.
    self.data_signals = [ i for i in xrange(0, self._nsignals)
                            if i not in self.annotation_signals ]

    #: The duration of the EDF file, in seconds.
    self.duration = self._datarecs*self._drduration

    #: The sample rate of each data signal, as samples/second.
    self.rate = [ n/float(self._drduration) for n in self.nsamples ]

    #: Scale and offset to convert from data block to physical values.
    self.scaling = [ ]
    for n in self.data_signals:
      try:
        scale = float(self._physmax[n] - self._physmin[n]) / float(self._digmax[n] - self._digmin[n])
        self.scaling.append( Scaling(scale, float(self._physmin[n]) - scale * float(self._digmin[n])) )
      except ZeroDivisionError:
        self._error('Physical max equal to minimum for signal %d: %s' % (n, self.label[n]))
        self.scaling.append( Scaling(1.0, 0.0) )

    self._offsets = [0]
    for i in xrange(1, self._nsignals):
      self._offsets.append(self._offsets[i-1] + 2*self.nsamples[i-1])
    self._recsize = self._offsets[self._nsignals-1] + 2*self.nsamples[self._nsignals-1]

    if self.filesize() != os.fstat(self._file.fileno()).st_size:
      self._error('File size mismatch -- expected %d, have %d bytes'
                  % (self.filesize(), os.fstat(self._file.fileno()).st_size))

    self.edf_type = (EDF.EDFplusC if self._reserved.startswith('EDF+C')
                else EDF.EDFplusD if self._reserved.startswith('EDF+D')
                else EDF.EDF)
    if self.edf_type != EDF.EDF:
      self._decode_patient()
      self._decode_recording()

    self._checkheader()


  def filesize(self):
  #------------------
    return self._hdrsize + self._datarecs * self._recsize

  def fixheader(self):
  #-------------------
    for i in xrange(0, self._nsignals):
      if self._digmin[i] == self._digmax[i] == 0:
        self._digmin[i] = -32768
        self._digmax[i] =  32767

  def writeheader(self):
  #---------------------
    ## Need self._nsignals set correctly...
    self._hdrsize = 256*(self._nsignals + 1)
    self._reserved = ('EDF+C' if self.edf_type == EDF.EDFplusC
                 else 'EDF+D' if self.edf_type == EDF.EDFplusD
                 else '')
    if self.edf_type != EDF.EDF:
      self._encode_patient()
      self._encode_recording()
    self._writeheader(self._file)


  def _error(self, msg):
  #---------------------
    self.errors.append(msg)

  def _getfield(self, t, data, n):
  #-------------------------------
    fld = data[n : n + t[1]].rstrip()
    if fld and fld[0] == ' ':
      self._error("Field '%s' is not left justified" % t[0])
      fld = fld.lstrip()
    try:
      return t[2](fld)
    except:
      if t[2] == str: return ''
      else:           return t[2](0)

  def _getfields(self, hdr, data, template, count=0):
  #--------------------------------------------------
    if nonprinting.search(data):
      self._error('Non printing characters in %s' % hdr)
      data = nonprinting.sub(' ', data)
    n = 0
    fields = { }
    for t in template:
      (f, l, typ) = t
      if count == 0:
        setattr(self, f, self._getfield(t, data, n))
        n += l
      else:
        fields = []
        for i in xrange(0, count):
          fields.append(self._getfield(('%s[%d]' % (f, i), l, typ), data, n))
          n += l
        setattr(self, f, fields)

  def _putfields(self, template, count=0):
  #---------------------------------------
    data = [ ]
    for (f, l, t) in template:
      fld = getattr(self, f)
      if count == 0: data.append(str(fld).lstrip().ljust(l))
      else:
        for i in xrange(0, count): data.append(str(fld[i]).lstrip().ljust(l))
    data = ''.join(data)
    ##data = nonprinting.sub(' ', data)
    if nonprinting.search(data): raise FormatError("Non printing characters in output")
    return data


  def _set_edfplus_fields(self, names, data):
  #------------------------------------------
    for n, f in enumerate(names):
      if data[n] != 'X': setattr(self, f, data[n])

  def _decode_patient(self):
  #-------------------------
    fields = self.patient.split()
    if len(fields) < 4: self._error("Corrupt EDF+ patient field")
    else:               self._set_edfplus_fields(PATIENTFIELDS, fields)
    ## self.patient = ' '.join(fields[4:])  ????

  def _decode_recording(self):
  #---------------------------
    fields = self.recording.split()
    if len(fields) < 5 or fields[0] != 'Startdate':
      self._error("Corrupt EDF+ recording field")
    else:
      self._set_edfplus_fields(RECORDINGFIELDS, fields[1:])
    ## self.recording = ' '.join(fields[5:])  ????


  def _get_edfplus_fields(self, names):
  #------------------------------------
    data = [ 'Startdate' ]
    for f in names:
      d = getattr(self, f, '').strip()
      data.append(d.replace(' ', '_') if d else 'X')
    return ' '.join(data)

  def _encode_patient(self):
  #-------------------------
    self.patient = self._get_edfplus_fields(PATIENTFIELDS)

  def _encode_recording(self):
  #---------------------------
    self.recording = self._get_edfplus_fields(RECORDINGFIELDS)


  def _checkheader(self):
  #----------------------
    for i in self.data_signals:
#      if self._physmin[i] >= self._physmax[i]:
#        self._error('Physical minimum is not less than maximum -- signal %d, %f >= %f'
#                    % (i, self._physmin[i], self._physmax[i]))
      if self._physmin[i] == self._physmax[i]:
        self._error('Physical minimum/maximum must be different -- signal %d, %f'
                    % (i, self._physmin[i]))
      if self._digmin[i] >= self._digmax[i]:
        self._error('Digital minimum is not less than maximum -- signal %d, %d >= %d'
                    % (i, self._digmin[i], self._digmax[i]))


  def _writeheader(self, output):
  #------------------------------
    output.seek(0)
    output.write(self._putfields(FILEHDR))
    output.write(self._putfields(SIGNALHDR, self._nsignals))


  def write_record(self, record):
  #------------------------------
    assert(record.dtype == np.short)
    self._file.write(str(record.data))


  def _get_range(self, interval=None):         ## Interval = (start, end) in seconds
  #----------------------------------          ## Returns ((first record, last record),
    if interval:                               ##          (offset first, offset last))
      recno = max(0, int(math.floor(interval[0]/self._drduration)))
      lastrec = min(self._datarecs, int(math.floor(interval[1]/self._drduration)))
      return ((recno, lastrec),
              (interval[0]/self._drduration - recno,  interval[1]/self._drduration - lastrec))
    else:
      return ((0, self._datarecs),
              (0.0, 0.0) )


  def annotations(self, interval=None):
  #-----------------------------------
    (recno, lastrec), (startratio, endratio) = self._get_range(interval)
    if endratio == 0.0: lastrec -= 1
    while recno <= lastrec:
      for n in self.annotation_signals:
        # An 'EDF Annotations' signal may contain multiple TALs.
        self._file.seek(self._hdrsize + recno*self._recsize + self._offsets[n])
        data = self._file.read(2*self.nsamples[n]).decode('utf-8') # Annotation is Unicode string   
        if data[-1] != '\x00': self._error("TAL doesn't end with NUL")
        else:
          for TAL in data.rstrip('\x00').split('\x00'):
            try: yield TimeStampedAnnotation(TAL)
            except FormatError, msg: self._error(msg)
      recno += 1

#### Record start must match annotations[0].onset
#### And annotations[0].annotations[0] must be empty...
      ##for a in annotations: print "Annotation DEBUG:", a   ###########
      ## Return annotations as metadata events...
      ##yield annotations  ## Just yield as they happen above...


  def _add_annotation_signal(self, maxsize):
  #-----------------------------------------
    signo = self._nsignals
    self.annotation_signals.append(signo)
    for f in SIGNALHDR: getattr(self, f[0]).append('')
    self.label[signo] = 'EDF Annotations'
    self._physmin[signo] = 0
    self._physmax[signo] = 1
    self._digmin[signo] = -32768
    self._digmax[signo] =  32767
    self.nsamples[signo] = (maxsize + 1)/2
    self._nsignals += 1
    self._offsets.append(self._offsets[signo-1] + 2*self.nsamples[signo-1])
    self._recsize += 2*self.nsamples[signo]
    return signo


  def _next_record(self, signals, interval, scaling):
  #--------------------------------------------------
    if not signals: signals = self.data_signals
    else:
      for n in signals:
        if n not in self.data_signals: raise InvalidSignalId()
    (recno, lastrec), (startratio, endratio) = self._get_range(interval)
    dtype = 'short' if scaling == None else 'float32'
    while recno <= lastrec:
      if recno == lastrec:
        if endratio == startratio: return
        proportion = endratio - startratio
      else:
        proportion = 1.0 - startratio
      for chan, signo in enumerate(signals):
        self._file.seek(self._hdrsize + recno*self._recsize
                      + self._offsets[signo] + 2*int(self.nsamples[signo]*startratio))
## _drduration*recno v's TAL onset
## No "ordinary signals"  <==>  len(self.data_signals) == 0
        sigstart = self._drduration*(recno + int(self.nsamples[signo]*startratio)/float(self.nsamples[signo]))
## What about on big-end system? PPC??
        raw = np.fromstring(self._file.read(2*int(self.nsamples[signo]*proportion)), np.short)
        if self.units[signo] == '' or scaling == None: data = raw
        else:
          if scaling:
            scale = float((scaling[1] - scaling[0]))/float(self._digmax[signo] - self._digmin[signo])
            offset = float(scaling[0]) - scale * float(self._digmin[signo])
          else:
            (scale, offset) = self.scaling[signo]
          data = scale * raw.astype(dtype) + offset
        yield RecordData(signo, sigstart, self.rate[signo], data)
      recno += 1
      startratio = 0.0


  def raw_records(self, signals=None, interval=None):
  #==================================================
    return self._next_record(signals, interval, None)

  def normalised_records(self, signals=None, interval=None, smin=-1.0, smax=1.0):
  #==============================================================================
    return self._next_record(signals, interval, (smin, smax))

  def physical_records(self, signals=None, interval=None):
  #=======================================================
    return self._next_record(signals, interval, ())

  def raw_signal(self, signum, posn, length):
  #=========================================
    if signum not in self.data_signals: raise InvalidSignalId()
    rsamples = self.nsamples[signum]
    startpos = int(max(0, min(posn, self._datarecs*self.nsamples[signum] - 1)))
    count    = int(max(0, min(min(length, length + posn), rsamples*self._datarecs - startpos)))
    #print rsamples, startpos, count
    recno = startpos / rsamples
    offset = startpos % rsamples
    pos = 0
    data = np.arange(0, dtype='short')
    while pos < count:
      n = min(count - pos, rsamples - offset)
      #print recno, offset
      self._file.seek(self._hdrsize + recno*self._recsize + self._offsets[signum] + 2*offset)
      data = np.append(data, np.fromstring(self._file.read(2*n), np.short))
      pos += n
      recno += 1
      offset = 0
    return SignalData(startpos, count, data)

  def normalised_signal(self, signum, posn, length, smin=-1.0, smax=1.0):
  #=====================================================================
    dmin = self._digmin[signum]
    dmax = self._digmax[signum]
    scale = float((smax - smin))/float(dmax - dmin)
    raw = self.raw_signal(signum, posn, length)
    return SignalData(raw.startpos, raw.length, smin + scale*raw.data - dmin)

  def physical_signal(self, signum, posn, length):
  #==============================================
    raw = self.raw_signal(signum, posn, length)
    return SignalData(raw.startpos, raw.length, self.scaling[signum].scale*raw.data + self.scaling[signum].offset)


"""

Logrithmic Transformation in EDF+
=================================

The  transformation does not cause any incompatibility with EDF
and  EDF+.  The  transformation  is  logarithmic  and symmetric
around  0.  It  has  user-selected  parameters  a  and Ymin. It
converts  floating-point  values, Y, to 2-byte integers, N. All
float  values  between  -Ymin  and Ymin are rounded to N=0. All
values  of  Y  larger  than  Ymin  and  smaller  than -Ymin are
logaritmically (with the LN being e-based) converted to N>0 and
N<0,   respectively.   The   obtained   integers,  N,  must  be
exponentially  (with the EXP also being e-based) converted back
to  to  the original float value, Y. The relative resolution of
this  conversion  is  constant,  i.e. Y(N)/Y(N-1) = EXP(a). The
exact conversion formulas are:

	                Float to Integer        	Integer back to Float
                 -----------------------  ---------------------
If Y>Ymin        N=round[LN(Y/Ymin)/a]    Y=Ymin*EXP(a*N)
If abs(Y)<=Ymin  N=0                     	Y=0
If Y<-Ymin       N=-round[LN(-Y/Ymin)/a] 	Y=-Ymin*EXP(-a*N)

So  that EDF and EDF+ software will be aware of the conversion,
the  "physical  dimension"  in  the EDF or EDF+ fileheader must
read  "Filtered".  The "physical maximum" = "digital maximum" =
"32767  ",  and  the  "physical  minimum"  =  "digital minimum"
="-32767  ".  Note  that digital minimum is -32767, not -32768.
The  parameters  a and Ymin can be chosen freely and have to be
specified,  together with the dimension of the original signal,
in  the  "prefiltering"  field of the header. This field should
contain   "sign*LN[sign*(physical   dimension)/(Ymin)]/(a)"  in
which  "physical  dimension"  and  the values of a and Ymin are
coded  in  arrays  of  8  ASCII  characters (left-justified and
filled  out  with spaces). For example if a=0.002 and Ymin=0.01
and   the   physical  dimension  of  Y  was  "uV  ",  then  the
prefiltering  field  should  contain:  sign*LN[sign*(uV )/(0.01
)]/(0.002 ).


"""
