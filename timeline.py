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


from biosignalml.rdf import TL, XSD

import biosignalml.utils as utils
import biosignalml.model as model
import biosignalml.model.mapping as mapping
from biosignalml.model.mapping import PropertyMap


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



from biosignalml.rdf import RDF, RDFS, DCTERMS, XSD

class Interval(model.core.AbstractObject):
#=========================================
  '''
  An abstract BioSignalML Interval.
  '''

  metaclass = TL.RelativeInterval  #: :attr:`.TL.RelativeInterval`

  attributes = [ 'timeline', 'start', 'duration' ]

  mapping = { ('timeline', metaclass): PropertyMap(TL.timeline,
                                                   to_rdf=mapping.get_uri,
                                                   from_rdf=TimeLine),
              ('start',    metaclass): PropertyMap(TL.beginsAtDuration, XSD.duration,
                                                   utils.seconds_to_isoduration,
                                                   utils.isoduration_to_seconds),
              ('duration', metaclass): PropertyMap(TL.durationXSD, XSD.duration,
                                                   utils.seconds_to_isoduration,
                                                   utils.isoduration_to_seconds) }

  def __init__(self, uri, start, duration, timeline, metadata=None):
  #-----------------------------------------------------------------
    model.core.AbstractObject.__init__(self, uri, metadata=metadata)
    self.start = start
    self.duration = duration
    self.timeline = timeline



  def __add__(self, increment):
  #----------------------------
    return Interval(self.make_uri(True), self.start + increment, self.duration, self.timeline)


class Instant(Interval):
#=======================
  '''
  An abstract BioSignalML Instant.
  '''

  metaclass = TL.RelativeInstant   #: :attr:`.TL.RelativeInstant`

  attributes = [ 'timeline', 'at' ]

  mapping = { ('timeline', metaclass): PropertyMap(TL.timeline,
                                                   to_rdf=mapping.get_uri,
                                                   from_rdf=TimeLine),
              ('at',       metaclass): PropertyMap(TL.atDuration, XSD.duration,
                                                   utils.seconds_to_isoduration,
                                                   utils.isoduration_to_seconds) }

  def __init__(self, uri, when, timeline, metadata=None):
  #------------------------------------------------------
    Interval.__init__(self, uri, when, 0.0, timeline, metadata=metadata)
    self.at = when


  def __add__(self, increment):
  #----------------------------
    return Instant(self.make_uri(True), self.at + increment, self.timeline)


