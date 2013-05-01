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
import math
from datetime import datetime, timedelta

from isodate  import isoduration
import dateutil.parser
from dateutil.tz import tzutc


__all__ = [ 'datetime_to_isoformat', 'isoformat_to_datetime', 'seconds_to_isoduration',
            'isoduration_to_seconds', 'utctime', 'utctime_as_string', 'expired', 'chop',
            'trimdecimal', 'maketime', 'cp1252', 'nbspescape', 'xmlescape', 'xml', 'num',
            'file_uri', 'hexdump', 'unescape' ]


def datetime_to_isoformat(dt):
#=============================
  """
  Convert a Python datetime to an ISO 8601 representation.

  :param dt: A Python :class:~`datetime.datetime`.
  :return: A string representation of the date and time formatted as ISO 8601.
  """
  iso = dt.isoformat()
  if iso.endswith('+00:00'): return iso[:-6] + 'Z'
  else:                      return iso

def isoformat_to_datetime(v):
#============================
  """
  Convert a string to a Python datetime.

  :param v: A string representing a date and time.
  :rtype: :class:~`datetime.datetime`
  """
  try:
    dt = dateutil.parser.parse(v)
    if dt.tzinfo is not None: return (dt - dt.utcoffset()).replace(tzinfo=tzutc())
    else:                     return dt
  except Exception, msg:
    logging.error("Cannot convert datetime '%s': %s", v, msg)
    return None

def seconds_to_isoduration(secs):
#================================
  """
  Convert a duration to an ISO 8601 representation.

  :param secs: The duration in seconds.
  :type secs: float
  :return: A string representation of the duration formatted as ISO 8601.
  """
  return isoduration.duration_isoformat(
    timedelta(seconds=int(secs), microseconds=int(1000000*(float(secs) - int(secs)) ))
    ) if secs != 0.0 else "PT0S"  ## More meaningful than "P0D"

def isoduration_to_seconds(d):
#=============================
  """
  Convert an ISO duration to a number of seconds.

  :param v: A string representing a duration, formatted as ISO 8601.
  :return: The number of seconds.
  :rtype: float
  """
  try:
    td = isoduration.parse_duration(d)
    return td.days*86400 + td.seconds + td.microseconds/1000000.0
  except:
    try: return float(d)    ## Virtuoso strips "PT" etc on import...
    except: return 0

def utctime():
#=============
  """
  Return the current UTC date and time.

  :rtype: :class:~`datetime.datetime`
  """
  return datetime.now(tzutc())

def utctime_as_string():
#=======================
  """
  Return the current UTC date and time formatted as ISO 8601.

  :rtype: str
  """
  return datetime_to_isoformat(utctime())

def expired(when):
#=================
  """
  Check if a datetime point has been reached.

  :param when: The Python :class:~`datetime.datetime` to test.
  :return: True if the time has been passed.

  """
  return (when and utctime() > when)


def chop(s, n):
#=============
  """Chop characters of the front of a string."""
  return str(s)[n:]

def trimdecimal(v):
#=================
  s = str(v)
  if '.' in s:
    s = s.rstrip('0')
    if s[-1] == '.': return s[:-1]
  return s

def maketime(secs):
#=================
  return trimdecimal(timedelta(seconds=secs))


def cp1252(s):
#============
  """ Encodes 's' as Unicode using cp1252 code table."""
  try:
    if isinstance(s, unicode): return s
    elif isinstance(s, str):   return s.decode('cp1252')
    else:                      return str(s).decode('cp1252')
  except Exception, e:
    logging.error("Can not encode %s", s)
    return('???')

def nbspescape(s):
#================
  return s.replace('&',
                   '&amp;').replace('<',
                                    '&lt;').replace('>',
                                                    '&gt;').replace('"',
                                                                    '&quot;').replace(' ',
                                                                                      '&#160;')

def xmlescape(s):
#===============
  if s:
    return s.replace('&',
                     '&amp;').replace('<',
                                      '&lt;').replace('>',
                                                      '&gt;').replace('"',
                                                                      '&quot;').encode('ascii',
                                                                                       'xmlcharrefreplace')
  else:
    return ''

def xml(x):
#=========
  r = []
  r.append('<' + x.__class__.__name__)
  for n, v in x.__dict__.iteritems(): r.append(' ' + n + '="' + xmlescape(str(v)) + '"')
  r.append('/>')
  return ''.join(r)


def num(n):
#=========
  """ Convert a string to an integer, returning 0 if
      the string isn't a valid integer."""
  if not isinstance(n, int):
    try: n = int(float(str(n)) + 0.5)
    except ValueError: n = 0
  return n


def file_uri(f):
#===============
  return f if f[0:5] in ['file:', 'http:'] else 'file://' + os.path.abspath(f)


def hexdump(s, prompt='', offset=0):
#==================================
  import string
  h = []
  h.append(offset*' ' + prompt)
  offset += len(prompt)
  s = ''.join(s)    #  Ensure a string
  l = len(s)
  sp = 0
  while l > 0:
    j = min(l, 16)
    tp = sp
    n = 0
    i = j
    while i > 0:
      h.append('%02X ' % ord(s[tp]))
      tp += 1 ;  i -= 1 ;  n += 1
    while n < 16:
      h.append('   ')
      n += 1
    h.append('  ')
    i = j
    tp = sp
    while i > 0:
      c = s[tp]
      if   string.whitespace.find(c) >= 0: h.append(' ')
      elif string.printable.find(c) >= 0:  h.append(c)
      else:                                h.append('.')
      tp += 1 ;  i -= 1
    l -= j
    sp += j
    if l > 0: h.append('\n' + offset*' ')
  return ''.join(h)

#############################################################
##
## From http://effbot.org/zone/re-sub.htm#unescape-html

import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":  # character reference
      try:
        if text[:3] == "&#x": return unichr(int(text[3:-1], 16))
        else:                 return unichr(int(text[2:-1]))
      except ValueError:
        pass
    else:                 # named entity
      try:
        text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text           # leave as is
  return re.sub("&#?\w+;", fixup, text)

##
#############################################################



if __name__ == '__main__':
#========================
  print utctime()
  print utctime_as_string()
  print hexdump('123\x01\x41B1234567890abcdefghijklmnopqrstuvwxyz')
