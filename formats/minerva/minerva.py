######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010 - 2011  David Brooks
#
#  $ID$
#
######################################################


import sys
import struct

from classes import Minerva, MinervaError


class _Header(object):
#====================
  pass


class MinervaFile(object):
#========================

  def __init__(self, fname):
  #------------------------
    self._file = None
    self._file = open(fname, 'rb')
    self._inheader = True
    self.header = _Header()

  def __del__(self):
  #----------------
    self.close()

  def close(self):
  #--------------
    if self._file: self._file.close()
    self._file = None

  def read_header(self):
  #--------------------
    while self._inheader:
      l = self._file.readline()[:-1]
      if l == 'data': self._inheader = False
      else:
        flds = l.split('-')
        key = flds[0].strip()
        d = getattr(self.header, key, {})
        for f in flds[1:]:
          s = f.split(' ', 1)
          v = s[1].strip() if len(s) > 1 else ''
          if s[0] == 'version':
            if v.find('.') == -1: v = '.'.join(v)
            elif v == '':         v = '0.0.0'
          d[s[0]] = v
        setattr(self.header, key, d)
    v = self.header.creator['version'].split('.')
    self._recode = (int(v[0]) <= 4 and int(v[1]) < 5)


  def get_bytes(self, s):
  #---------------------
    d = self._file.read(len(s))
    if d != s: raise MinervaError('File has wrong format')

  def read_until(self, byte):
  #--------------------------
    while self._file.read(1) != byte:
      pass

  def read_byte(self):
  #------------------
    return struct.unpack('<B', self._file.read(1))[0]

  def read_short(self):
  #-------------------
    return struct.unpack('<h', self._file.read(2))[0]

  def read_int(self):
  #-----------------
    return struct.unpack('<i', self._file.read(4))[0]

  def read_float(self):
  #-------------------
    return struct.unpack('<f', self._file.read(4))[0]

  def read_data(self, format, length):
  #----------------------------------
    return struct.unpack(format, self._file.read(length))


class EventFile(MinervaFile):
#===========================

  def _make_event(self, starttime, duration, channel, typ, cls, mode, posn, flags):
  #-------------------------------------------------------------------------------
    if self._recode: evt = Minerva.recoded_event(typ, cls, flags)
    else:            evt = Minerva.event(typ, cls)
    return ((starttime, duration), channel, evt, (mode, posn, flags))


  def read_events(self):
  #--------------------
    self.get_bytes('\x3a\x01\x01\x00\x00')
    eventcount = self.read_int()
    eventlist = [ ]
    while eventcount > 0:
      self.get_bytes('\x5b\x05\x00\x00\x00\x45\x76\x65\x6e\x74\x01\x00\x00\x00')
      eventlist.append(self._make_event(*self.read_data('<ffiiiiih', 30)))
      self.read_until('\x5d')
      eventcount -= 1
    return eventlist


class HypnogramFile(MinervaFile):
#===============================

  def read_events(self):
  #--------------------
    laststage = -1
    lastcomputed = -1
    seconds    = 0                 # Sleep scored every 10 seconds
    sleepstart = 0
    sleeplen   = 0                 # Seconds
    sleeplist = [ ]

    while len(self._file.read(4)) == 4: # Skip unused 4 bytes and check for EOF
      stage = self.read_byte()
      computed = self.read_byte()
      if stage != laststage or computed != lastcomputed:
        if sleeplen > 0:
          if laststage != 255:
            sleeplist.append( ((sleepstart, sleeplen), -1, Minerva.sleepstage(laststage), None) )
          sleepstart = seconds
          sleeplen = 0
        laststage = stage
        lastcomputed = computed
      sleeplen += 10
      seconds += 10
    if sleeplen > 0 and laststage != 255:
      sleeplist.append( ((sleepstart, sleeplen), -1, Minerva.sleepstage(laststage), None) )
    return sleeplist


#      ann.setProperty(DCTERMS.source, new File(file).toURI())
#      ann.setProperty(DCTERMS.creator, "%s Version: %d".format(creator_name, creator_version))
#      ann.setProperty(DCTERMS.created, study_date)
#      ann.setProperty(TL.beginsAtDateTime, Time.getCalendarDateTime(starttime, 0))
#      ann.setProperty(DCTERMS.description, "Study: " + study_id)

#    for (evt <- eventset.events) {
#      val signal = recording.getSignal(evt.channel.toString)

#      val interval = new Interval(evt.starttime.toDouble, evt.duration.toDouble, recording.timeline)
#      val event = signal.addEventInterval("minerva_" + eventno.toString, interval)

#      event.setProperty(RDF.rdftype,      CLASS.toRDF(evt.eventtype, evt.eventclass))


#      if (evt.mode != 0)      event.setProperty(MEVENT.mode,     evt.mode)
#      if (evt.position != -1) event.setProperty(MEVENT.position, evt.position)
#      if (evt.flags != 0)     event.setProperty(MEVENT.flags,    FLAG.toString(evt.flags))

#Event
#  Event_type1
#    Event_type1_class1
#    Event_type1_class2
#    Event_type1_class3
#  Event_type2
#    Event_type2_class1
#    Event_type2_class2

#    event_N
#      a Event_type_class
#      event:time [
#        tl:timeline etc
#        ]
#      bsml:signal ...



if __name__ == '__main__':
#========================
  """
  from bsml import Recording, Signal
  from metadata import Uri

  base = 'http://repository.biosignalml.org/recording/'  # From INI file

  rec = Recording.create(Uri(base + sys.argv[1]))

  m = EventFile(sys.argv[2])
  m.read_header()

  events = m.read_events()
  for n, e  in enumerate(events):
    id = 'minerva_%d' % (n + 1)
    sig = Signal(rec, id=str(e[1]))
    sig.event(id, e[2], rec.interval(*e[0]))

  print rec.serialise(Uri(base), format='turtle')



###  repository.add_statements(events.as_stream(), context=recording)
  """




  m = EventFile(sys.argv[1])
  m.read_header()

  events = m.read_events()
  for n, e  in enumerate(events):
    print str(e[2]).rsplit('#', 1)[1], e[0][0], e[0][1]
    if n > 10: break
