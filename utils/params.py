######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################

from pyparsing import *
from optparse import OptionParser


class InvalidTime(Exception):
#============================
  pass

def getsecs(s, l, t):
#====================
  return [float(t[0])]

def getmmss(s, l, t):
#====================
  tm = t[0].split(':')
  if float(tm[1]) > 60.0: raise InvalidTime('Invalid time')
  return [60.0*float(tm[0]) + float(tm[1])]

def gethhmmss(s, l, t):
#====================
  tm = t[0].split(':')
  if float(tm[1]) > 60.0 or float(tm[2]) > 60.0: raise InvalidTime('Invalid time')
  return [3600.0*float(tm[0]) + 60.0*float(tm[1]) + float(tm[2])]


integer      = Word(nums).setParseAction(lambda s,l,t: [int(t[0])])

seconds      = Combine(integer + Optional('.'  + Word(nums))).setParseAction(getsecs)
hhmmss       = Combine(integer + ':' + integer + ':' + seconds).setParseAction(gethhmmss)
mmss         = Combine(                integer + ':' + seconds).setParseAction(getmmss)

time         = hhmmss | mmss | seconds
timerange    = Group(time + '-' + time)
timeduration = Group(time + '/' + time)

timelist     = delimitedList(timerange | timeduration)


sigid    = Word(srange("[1-9]"), nums).setParseAction(lambda s,l,t: [int(t[0])])
sigrange = Group(sigid + Suppress('-') + sigid)
siglist  = delimitedList(sigrange | sigid)


def parse(parser, s):
#====================
  try:
    return parser.parseString(s)
  except AttributeError:
    return [ ]
#  except ParseException:
#    return [ ]


def timerange(s):
#================
  """Parse a comma separated list of time ranges.

  Each time range is in the form of "<start> - <end>" or "<start> / <duration>" where
  <start>, <end> and <duration> are all of the form "HHHHH:MM:SS.sss", SSSS.ssss MMMMM:SS.ssss

  :param string s: the string to parse.
  :return list: a list of time intervals.
  """
  times = list()
  for tm in parse(timelist, s):
    if isinstance(tm, ParseResults):
      if   tm[1] == '-':
        start = tm[0]
        end   = tm[2]
        if end < start: raise InvalidTime('Interval ends before start')
      elif tm[1] == '/':
        start = tm[0]
        end   = start + tm[2]
    else:
      start = tm
      end = start
    times.append((start, end))
  times.sort()
  return times


def signalrange(s, origin=1):  ## What about param to control if sorted...?????
#===========================
  """

  "a, b, n - m" -->  [a, b, n, n+1, ..., m]

  """
  offset = origin - 1
  sigs = list()
  for id in parse(siglist, s):
    if isinstance(id, ParseResults):
      if id[0] <= id[1]: sigs.extend(xrange(id[0], id[1]+1))
      else:              sigs.extend(xrange(id[1], id[0]+1))
    else:
      sigs.append(id)
  #sigs = list(set(sigs))  ## removes duplicates...
  #sigs.sort()
  return [ (s + offset) for s in sigs ] if offset else sigs


if __name__ == '__main__':
#=========================

  def parseArguments():
  #====================
    global options
    parser = OptionParser(usage='usage: %prog [options]',
                          description='Test parsing of signal and time ranges.')
    parser.add_option("-t", "--times", dest="times")
    parser.add_option("-s", "--signals", dest="signals")
    (options, args) = parser.parse_args()
    return (options, args)


  """
  def testparse(parser, s):
  #========================
    print '"%s" -> %s' % (s, parse(parser, s))

  testparse(siglist, '1, 2, 3')
  testparse(siglist, '1, 10 - 13')
  testparse(siglist, '1, 10-13, 6')
  testparse(siglist, 'A1, 10-13, 6')
  print ''

  testparse(seconds, '1. 2')
  testparse(seconds, '0.2')
  testparse(seconds, '2')
  testparse(delimitedList(time), '0.1, 0.2')
  testparse(delimitedList(time), '1:0.1,1:0.2')
  testparse(delimitedList(time), '1:0.1, 1:0.2')
  print ''

  testparse(timelist, '1:0.1 - 1:0.2')
  testparse(timelist, '.1')
  testparse(timelist, '1')
  testparse(timelist, '1.2')
  testparse(timelist, '1:2')
  testparse(timelist, '1:2:3')
  testparse(timelist, '1:2:3.4')
  testparse(timelist, '1: 2:3')
  testparse(timelist, '1:2:3, 4')
  testparse(timelist, '1:2:3, 4:10-5:50, 12/3')
  """

  options, args = parseArguments()
  print 'Signals:',   signalrange(options.signals)
  print 'Intervals:', timerange(options.times)
