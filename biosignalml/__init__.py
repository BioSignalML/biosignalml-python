'''
BioSignalML data model.
'''
######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
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

__version__ = '0.4.0'

from ontology import BSML

import biosignalml.data  as data
import biosignalml.model as model

from model import Recording, Event, Annotation, Segment


class Signal(model.Signal, data.TimeSeries):  ## TEST WHAT MIXIN ENABLES...
#===========================================

  ##def __init__(self, 

  def read(self, interval=None, **kwds):
  #-------------------------------------
    '''
    :return: A :class:TimeSeries containing signal data covering the interval.
    '''
    raise NotImplementedError, 'Signal.read()'


class UniformSignal(Signal, data.UniformTimeSeries):
#===================================================

  @classmethod
  def create(cls, uri, units, rate=None, period=None, **kwds):
  #------------------------------------------------------------
    self = cls(uri, units, rate=rate, period=period, **kwds)


## from client import Repository   ## Needs to be after Signal has been declared
