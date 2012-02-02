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
#  $ID: bbd3c04 on Wed Jun 8 16:47:09 2011 +1200 by Dave Brooks $
#
######################################################

from abstraction import *
from timeline    import *
from data        import *
from ontology    import BSML



class Recording(AbstractRecording):
#==================================
  pass


class Signal(AbstractSignal, TimeSeries):
#========================================

  ##def __init__(self, 

  def read(self, interval):
  #------------------------
    '''
    :return: A :class:TimeSeries containing signal data covering the interval.
    '''
    raise NotImplementedError, 'Signal.read()'




  def __len__(self):
  #----------------
    return 0


class UniformSignal(Signal, UniformTimeSeries):
#==============================================
  pass


class Event(AbstractEvent):
#==========================
  pass
