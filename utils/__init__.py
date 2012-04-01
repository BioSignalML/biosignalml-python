######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################

import os
import math
import datetime


def now():
#========
  t = str(datetime.datetime.now())
  dp = t.find('.')
  if dp > 0: return t[:dp]
  else:      return t

def expired(when):
#================
  return (when and str(datetime.datetime.now())[0:10] > when)

def chop(s, n):
#=============
  return str(s)[n:]

def trimdecimal(v):
#=================
  s = str(v)
  return s.rstrip('0')[:-1] if '.' in s else s

def maketime(secs):
#=================
  return trimdecimal(datetime.timedelta(seconds=secs))


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
  return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace(' ', '&#160;')

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
  return f if f.startswith('file:') else 'file://' + os.path.abspath(f)


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
  print now()
  print hexdump('123\x01\x41B1234567890abcdefghijklmnopqrstuvwxyz')
