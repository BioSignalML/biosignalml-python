######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


import pyparsing as pp
import numpy as np
import math
import logging


## PyParsing grammer for SDF header lines.

ident   = pp.Word(pp.alphas, pp.alphanums).setParseAction(lambda s,l,t: [t[0].lower()])

unicodePrintables = u''.join(unichr(c) for c in xrange(65536) if not unichr(c).isspace())

text    = pp.Word(unicodePrintables)
string  = pp.QuotedString('"') | pp.QuotedString("'")

integer = pp.Combine(pp.Optional(pp.oneOf("+ -")) + pp.Word(pp.nums)).setParseAction(lambda s,l,t: [int(t[0])])
real    = pp.Combine(integer + "." + pp.Optional(pp.Word(pp.nums))
                   + pp.Optional(pp.oneOf("e E") + integer)).setParseAction(lambda s,l,t: [float(t[0])])
number  = real | integer
bool    = pp.CaselessLiteral('true').setParseAction(lambda s,l,t: [True]
      ) | pp.CaselessLiteral('false').setParseAction(lambda s,l,t: [False])

date    = pp.Combine(pp.Word(pp.nums)
          + pp.oneOf('. /') + pp.Word(pp.nums)
          + pp.oneOf('. /') + pp.Word(pp.nums))

time    = (  pp.Combine(integer + ':' + pp.Word(pp.nums))
           | pp.Combine(integer + ':' + pp.Word(pp.nums) + '.' + pp.Word(pp.nums))
           | pp.Combine(integer + ':' + pp.Word(pp.nums) + ':' + pp.Word(pp.nums))
           | pp.Combine(integer + ':' + pp.Word(pp.nums) + ':' + pp.Word(pp.nums) + '.' + pp.Word(pp.nums))
          )

fname   = pp.Combine(text + '.' + text) | pp.Combine(text + '.')

##value   = string | date | time | fname | number | bool | text
value   = string | bool | text

keyvalue = pp.Group(pp.Combine(pp.Suppress('-') + ident) + value)

hdrline  = ident + pp.OneOrMore(keyvalue)



class SDFFile(object):
#=====================

  def __init__(self, fname):
  #-------------------------
    super(SDFFile, self).__init__()
    self._file = open(fname, 'rb')    ## 'r' will give us unicode under Python 3...
    while True:
      l = self._file.readline().rstrip()
      ##logging.debug('Read: %s', l)
      if l.lower() in ['', 'data']: break
      try:
        l = l.replace('\xb5', '\xc2\xb5')  # Window's micron to Unicode
        p = hdrline.parseString(l)
        self.store_fields(p[0], p[1:])
      except pp.ParseException, msg:
        pass
    self._dataoffset = self._file.tell()

  def close(self):
  #---------------
    self._file.close()

  def store_fields(self, key, flds):       # Override in subclasses
  #---------------------------------
    self._save_data(key, flds)

  def _save_data(self, key, flds, otype=dict):
  #-------------------------------------------
    try: s = getattr(self, key)
    except AttributeError:
      s = otype()
      setattr(self, key, s)
    if   otype == dict: o = s
    elif otype == list:
      o = dict()
      s.append(o)
    for f in flds: o[f[0]] = f[1]


class ControlFile(SDFFile):
#=========================

  def __init__(self, fname):
  #-------------------------
    self.datafile = [ ]
    self.eventfile = [ ]
    super(ControlFile, self).__init__(fname)

  def store_fields(self, key, flds):
  #---------------------------------
    if key in ['patient', 'recording']: self._save_data(key, flds)
    else:                               self._save_data(key, flds, list)


class DataFile(SDFFile):
#=======================

  def __init__(self, fname):
  #-------------------------
    super(DataFile, self).__init__(fname)

    ascii = getattr(self, 'ascii', None)
    binary = getattr(self, 'binary', None)
    if ascii is None:
      if binary is None:
        self.ascii = True       # Default to ASCII
        self.binary = False
      else:
        self.ascii = not binary
    else:
     if   binary is None:
       self.binary = not ascii
     elif ascii == binary:
       raise Exception("'%s' signal cannot be both binary and Ascii" % fname)
    dtype = getattr(self, 'type', '').lower()
    bytes = int(getattr(self, 'bytes', 0))
    format = None
    if   dtype == 'char':
      if bytes in [0, 1]: format = 'i1'
    elif dtype in ['int', 'integer', 'binary']:
      if   bytes == 1: format = 'i1'
      elif bytes == 2: format = 'i2'
      elif bytes == 4: format = 'i4'
      elif bytes == 8: format = 'i8'
      elif bytes == 0: format = 'i4'    # default
    elif dtype == 'long':
      if   bytes == 4: format = 'i4'
      elif bytes == 8: format = 'i8'
      elif bytes == 0: format = 'i4'    # default  ???
    elif dtype == 'float':
      if   bytes == 4: format = 'f4'
      elif bytes == 8: format = 'f8'
      elif bytes == 0: format = 'f4'    # default  ???
    elif dtype == 'double':
      if bytes in [0, 8]: format = 'f8'
    if format and format[0] == 'i' and not getattr(self, 'signed', True):
      format = 'u' + format[1:]
    if self.ascii:
      if format is None: format = 'f8'  # default
      self._dtype = np.dtype(format)
    else:                               # binary:
      if format is None:
        raise Exception("Missing or invalid type and/or byte size for '%s'" % fname)
      endness = getattr(self, 'storage', '')
      if   endness == 'big-endian':    self._dtype = np.dtype('>' + format)
      elif endness == 'little-endian': self._dtype = np.dtype('<' + format)
      else:                            self._dtype = np.dtype(format)
    if not getattr(self, 'samplingrate', 0):
      raise Exception("Missing sample rate for '%s'" % fname)
    self.samplingrate = float(self.samplingrate)
    self._datastart = 0.0


  def store_fields(self, key, flds):
  #---------------------------------
    if key == 'data':
      for f in flds: setattr(self, f[0], f[1])
    else:
      self._save_data(key, flds)


  def read_data(self, starttime, duration):
  #----------------------------------------
    if self.ascii:
      starttime = self._datastart
      data = np.fromstring(self._file.read(), dtype=self._dtype, sep=' ')
      # This reads entire file
      # Could return lines with self._file.readline() using yield
      self._starttime += data.size*self.samplingrate
    else:              # binary:
      bytespersecond = self.samplingrate*self._dtype.itemsize
      self._file.seek(self._dataoffset + starttime*bytespersecond)
      data = np.fromstring(self._file.read(int(math.ceil(duration*bytespersecond))),
                           dtype=self._dtype)
      ##  raw = np.fromfile ?????????????????????
      ##  raw = np.fromstring(self._file.read(bytes), dtype=self._dtype)
    return (starttime, self.samplingrate, data)


class EventFile(SDFFile):
#=======================

  def __init__(self, fname, label):
  #--------------------------------
    super(EventFile, self).__init__(fname)
    self._label = label

  def store_fields(self, key, flds):
  #---------------------------------
    if key == 'event':
      if len(flds) and flds[0][0] == 'variable':
        self._save_data('event', flds, list)
      else:
        for f in flds: setattr(self, f[0], f[1])
    else:
      self._save_data(key, flds)
