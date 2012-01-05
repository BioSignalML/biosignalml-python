import struct


class Type(object):
#==================

# Rig types:
  MIXED   = -1
  SOCK    =  0
  PATCH   =  1
  TORSO   =  2
  UNKNOWN =  3


class Signal(object):
#====================

  ACCEPTED = 0
  REJECTED = 1
  UNDECIDED = 2

  def __init__(self, index, status):
  #---------------------------------
    self._index = index
    self._status = status


class Electrode(object):
#=======================

  def __init__(self, x, y, z=None):
  #--------------------------------
    self._position = (x, y) if z is None else (x, y, z)

  def __str__(self):
  #-----------------
    return str(self._position)



class Auxilary(object):
#======================

  DEVICE_CHANNEL    = 0
  DEVICE_EXPRESSION = 1
  DEVICE_SUM        = 2

  def __init__(self, weight, electrode_no):
  #----------------------------------------
    self._weight = weight
    self._electrode_no = electrode_no


class Channel(object):
#=====================

  def __init__(self, number):
  #--------------------------
    self._number = number
    self._gain = 1.0
    self._offset = 0.0

  def set(self, gain, offset):
  #---------------------------
    self._gain = gain
    self._offset = offset


class Page(object):
#==================

  def __init__(self, rdr, rig):
  #----------------------------
    pass


class Device(object):
#====================

# Device types:
  ELECTRODE = 0
  AUXILIARY = 1

  def __init__(self, rdr, region):
  #-------------------------------
    self._region = region
    self._type = rdr.getint()
    self._number =  rdr.getint()
    self._name  = rdr.getstring()
    self._channel = None
    self._electrode = None
    self._auxdevices = [ ]
    self._signals = [ ]

    if   self._type == Device.AUXILIARY:
      auxtype = rdr.getint()
      if   auxtype == Auxiliary.DEVICE_CHANNEL:
        self._channel = Channel(channel_no)
      elif auxtype == Auxiliary.DEVICE_EXPRESSION:
        self._expression = rdr.getstring()
      elif auxtype == Auxiliary.DEVICE_SUM:
        for e in xrange(rdr.getint()):
          self._auxdevices.append(Auxiliary(rdr.getfloat(), rdr.getint()))
      else:
        raise Exception, "Unknown Auxiliary device type (%d)" % auxtype

    channel_no = rdr.getint()
    if   self._type == Device.AUXILIARY:
      if channel_no < 0:
        for e in xrange(-channel_no):
          self._auxdevices.append(Auxiliary(rdr.getfloat(), rdr.getint()))
      else:
        self._channel = Channel(channel_no)
        
    elif self._type == Device.ELECTRODE:
      self._channel = Channel(channel_no)
      if   region._type == Type.SOCK or region._type == Type.TORSO:
        self._electrode = Electrode(rdr.getfloat(), rdr.getfloat(), rdr.getfloat())
      elif region._type == Type.PATCH:
        self._electrode = Electrode(rdr.getfloat(), rdr.getfloat())
      else:
        raise Exception, "Cannot create Electrode channel"

    else:
      raise Exception, "Unknown device type (%d) (%s)" % (self._type, hex(rdr.tell()))

  def __str__(self):
  #-----------------
    return "DEVICE: %s, type=%d at %s, signals: %s" % (self._name, self._type, self._electrode,
                                         ', '.join([str(s._index) for s in self._signals]))


class Region(object):
#====================

  def __init__(self, rdr, rig):
  #----------------------------
    self._type  = (rdr.getint() if rig._type == Type.MIXED
                 else
                   rig._type)
    self._name  = rdr.getstring()
    self._focus = (rdr.getfloat() if rig._type == Type.MIXED and self._type == Type.SOCK
                 else
                   rig._focus)
    for d in xrange(rdr.getint()):
      rig._devices.append(Device(rdr, self))

  def __str__(self):
  #-----------------
    return "REGION: %s, type=%d" % (self._name, self._type)

 
class Reader(object):
#====================

  def __init__(self, f, low, high):
  #--------------------------------
    self._file = f

  def tell(self):
  #--------------
    return self._file.tell()

  def seek(self, offset, whence=0):
  #--------------------------------
    return self._file.seek(offset, whence)

  def getint(self):
  #----------------
    s = self._file.read(4)
    return struct.unpack('>i', s)[0]

  def getshort(self):
  #-------------------
    s = self._file.read(2)
    return struct.unpack('>h', s)[0]

  def getfloat(self):
  #-------------------
    s = self._file.read(4)
    return struct.unpack('>f', s)[0]

  def getstring(self):
  #------------------
    return self._file.read(self.getint())


class Rig(object):
#=================

  def __init__(self, f):
  #---------------------
    rdr = Reader(f, Type.MIXED, Type.UNKNOWN)

    self._type = rdr.getint()
    if not (Type.MIXED <= self._type <= Type.UNKNOWN):
      raise Exception, "Bad file -- Unknown type of UnEmap rig"

    self._name = rdr.getstring()
    self._focus = rdr.getfloat() if self._type == Type.SOCK else None
    self._regions = [ ]
    self._devices = [ ]
    for r in xrange(rdr.getint()):
      self._regions.append(Region(rdr, self))
    self._pages = [ ]
    for p in xrange(rdr.getint()):
       self._pages.append(Page(rdr, self))

    self._nsignals = rdr.getint()
    if self._nsignals < 0:
      self._sigtype = 'f'
      self._nsignals = -self._nsignals
    else:
      self._sigtype = 'h'

    self._nsamples = rdr.getint()
    self._frequency = rdr.getfloat()

    # Now have array of times, followed by signal data
    # Can skip over this (as know size) to get signal scaling
    self._timeposition = rdr.tell()
    self._dataposition = self._timeposition + 4*self._nsamples  # sizeof(int) = 4
    rdr.seek(self._dataposition + (4 if self._sigtype == 'f' else 2)*self._nsamples*self._nsignals)

##    print self._nsamples, self._nsignals, self._sigtype, hex(self._timeposition), hex(self._dataposition), hex(rdr.tell())

    for d in self._devices:
      if d._channel is not None:
        index = rdr.getint()
        offset = rdr.getfloat()
        gain = rdr.getfloat()
        if gain > 0: d._channel.set(gain, offset)
        else:        d._channel.set(1.0, 0.0)
        d._signals.append(Signal(index if index >= 0 else -(index+1),
          Signal.UNDECIDED if d._type == Device.ELECTRODE else Signal.REJECTED))
        while index < 0:
          index = rdr.getint()
          d._signals.append(Signal(index if index >= 0 else -(index+1),
            Signal.UNDECIDED if d._type == Device.ELECTRODE else Signal.REJECTED))


  def __str__(self):
  #-----------------
    text = []
    text.append("RIG: %s, type=%d" % (self._name, self._type))
    text.append("\nRegions:")
    for r in self._regions: text.append('  %s' % r)
    text.append("\nDevices:")
    for d in self._devices: text.append('  %s' % d)
    return '\n'.join(text)


if __name__ == '__main__':
#=========================

  import sys

  rig = Rig(open(sys.argv[1], 'rb'))

  print rig
