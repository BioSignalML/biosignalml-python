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
'''
A BioSignalML Signal.
'''

import logging

import biosignalml.utils as utils
from biosignalml.rdf import XSD, DCT

from .ontology import BSML
from .core     import AbstractObject
from .mapping  import PropertyMap
from .segment  import Segment

__all__ = [ 'Signal' ]


class Signal(AbstractObject):
#============================
  """
  An abstract BioSignalML Signal.

  :param uri: The URI of the signal.
  :param units: The physical units of the signal's data.
  :param kwds: Signal attributes, specified as keywords.
  """

  metaclass = BSML.Signal     #: :attr:`.BSML.Signal`

  attributes = ['recording', 'units', 'transducer', 'filter', '_rate',  '_period', 'clock',
                'minFrequency', 'maxFrequency', 'minValue', 'maxValue',
                'index', 'signaltype', 'offset', '_duration', '_time_units',
               ]              #: Generic attributes of a Signal.

  mapping = { 'recording':    PropertyMap(BSML.recording, to_rdf=PropertyMap.get_uri),
              'units':        PropertyMap(BSML.units, to_rdf=PropertyMap.get_uri),
              'sensor':       PropertyMap(BSML.sensor),
              'filter':       PropertyMap(BSML.preFilter),
              '_rate':        PropertyMap(BSML.rate, XSD.double),
              '_period':      PropertyMap(BSML.period, XSD.double),
              'clock':        PropertyMap(BSML.clock, to_rdf=PropertyMap.get_uri, subelement=True),
              'minFrequency': PropertyMap(BSML.minFrequency, XSD.double),
              'maxFrequency': PropertyMap(BSML.maxFrequency, XSD.double),
              'minValue':     PropertyMap(BSML.minValue, XSD.double),
              'maxValue':     PropertyMap(BSML.maxValue, XSD.double),
              'dataBits':     PropertyMap(BSML.dataBits, XSD.integer),
              'signaltype':   PropertyMap(BSML.signalType),
              'offset':       PropertyMap(BSML.offset, XSD.dayTimeDuration,
                                          utils.seconds_to_isoduration,
                                          utils.isoduration_to_seconds),
              '_duration':    PropertyMap(DCT.extent, XSD.dayTimeDuration,
                                          utils.seconds_to_isoduration,
                                          utils.isoduration_to_seconds),
            }

  def __init__(self, uri, units, **kwds):
  #--------------------------------------
    rate = kwds.pop('rate', None)
    period = kwds.pop('period', None)
    if rate is not None and period is not None and float(rate) != 1.0/float(period):
      raise ValueError("Signal's sampling rate doesn't match its period")
    kwds['_rate'] = rate
    kwds['_period'] = period
    AbstractObject.__init__(self, uri, units=units, **kwds)

  def __len__(self):
  #----------------
    return 0

  def __nonzero__(self):
  #---------------------
    return True  # Otherwise bool(sig) is False, because we have __len__()

  @property
  def rate(self):
  #==============
    """The signal's sampling rate, in 1/:attr:`time_units`"""
    if   self._rate   is not None: return float(self._rate)
    elif self._period is not None: return 1.0/float(self._period)

  @property
  def period(self):
  #================
    """The signal's sampling period, in :attr:`time_units`."""
    if   self._period is not None: return float(self._period)
    elif self._rate   is not None: return 1.0/float(self._rate)

  @property
  def duration(self):
  #------------------
    """The signal's total duration, in :attr:`time_units`."""
    if self._duration is not None: return self._duration
    elif self.period is not None: return len(self)*self.period
    ## self.time[-1] + (self.period if self.period is not None else 0)  ???

  @property
  def time_units(self):
  #====================
    """The units used for signal timing. Default units are seconds"""
    return getattr(self, '_time_units', units.get_units_uri('s'))

  def new_segment(self, uri, at, duration=None, end=None, **kwds):  ## Of a Signal
  #---------------------------------------------------------------
    """
    Create a new :class:`~.segment.Segment` of a Signal.

    :param uri: The URI of the Segment.
    :param float at: When the segment starts.
    :param float duration: The duration of the Segment. Optional.
    :param float duration: When the Segment ends. Optional.
    :param kwds: Optional additional attributes for the Segment.

    """
    return self.recording.add_resource(
             Segment(uri, self, self.recording.interval(at, duration, end), **kwds))
