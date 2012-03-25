'''
TimeLine, Instant and Interval objects.
'''
######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
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
#  $ID: bbd3c04 on Wed Jun 8 16:47:09 2011 +1200 by Dave Brooks $
#
######################################################


from biosignalml.rdf import TL

import model


class TimeLine(model.core.AbstractObject):
#=========================================

  '''
  An abstract BioSignalML TimeLine.
  '''

  metaclass = TL.RelativeTimeLine  #: :attr:`.TL.RelativeTimeLine`

  def instant(self, when):
  #----------------------
    return Instant(self.make_uri(), when, self)

  def interval(self, start, duration):
  #----------------------------------
    if duration == 0.0: return self.instant(start)
    else:               return Interval(self.make_uri(), start, duration, self)


class Instant(model.core.AbstractObject):
#========================================
  '''
  An abstract BioSignalML Instant.
  '''

  metaclass = TL.RelativeInstant   #: :attr:`.TL.RelativeInstant`

  def __init__(self, uri, when, timeline, metadata={}):
  #----------------------------------------------------
    model.core.AbstractObject.__init__(self, uri, metadata=metadata)
    self._at = when
    self.timeline = timeline

  @property
  def at(self, timeline=None):     # Needs to use timeline to map
  #---------------------------
    return self._at

  def __add__(self, increment):
  #----------------------------
    return Instant(self.make_uri(True), self._at + increment, self.timeline)


class Interval(model.core.AbstractObject):
#=========================================
  '''
  An abstract BioSignalML Interval.
  '''

  metaclass = TL.RelativeInterval  #: :attr:`.TL.RelativeInterval`

  def __init__(self, uri, start, duration, timeline, metadata={}):
  #---------------------------------------------------------------
    model.core.AbstractObject.__init__(self, uri, metadata=metadata)
    self._start = start
    self._duration = duration
    self.timeline = timeline

  @property
  def start(self, timeline=None):     # Needs to use timeline to map
  #------------------------------
    return self._start

  @property
  def duration(self, timeline=None):  # Needs to use timeline to map
  #---------------------------------
    return self._duration

  def __add__(self, increment):
  #----------------------------
    return Interval(self.make_uri(True), self._start + increment, self._duration, self.timeline)


