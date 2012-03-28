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


from ontology import BSML

import biosignalml.data  as data
import biosignalml.model as model

class Recording(model.AbstractRecording):
#========================================
  pass


class Signal(model.AbstractSignal, data.TimeSeries):
#===================================================

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

  def __nonzero__(self):
  #---------------------
    return True  # Otherwise bool(sig) is False, because we have __len__()


class UniformSignal(Signal, data.UniformTimeSeries):
#===================================================

  @classmethod
  def create(cls, uri, units, rate):
  #---------------------------------
    self = cls(uri, units, rate=rate)


class Event(model.AbstractEvent):
#================================
  pass


class Annotation(model.AbstractAnnotation):
#==========================================
  pass


from client import Repository
#============================
