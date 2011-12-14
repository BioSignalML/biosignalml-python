######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID: c9e447e on Wed Mar 3 12:53:44 2010 +1300 by dave $
#
######################################################


"""
Provide access to BioSignalML model.

"""

##from bsml      import BSML  # What about a 'namespace' module?

# Our own namespace:  (put into metadata package...)

from rdfmodel import Uri, Resource, NS as Namespace

class BSML(object):
  uri = Uri('http://www.biosignalml.org/ontologies/2011/04/biosignalml#')
  NS = Namespace(str(uri))

# m = RDF.Model()
# m.load('file:./biosignalml2.owl')
# c = m.get_sources(rdf.type, owl.Class)
# for i in c: print(str(i))

# owl:Classes:
  Annotation    = Resource(NS.Annotation)
  BP_Filter     = Resource(NS.BP_Filter)
  Dataset       = Resource(NS.Dataset)
  Device        = Resource(NS.Device)
  Filter        = Resource(NS.Filter)
  Format        = Resource(NS.Format)    ## Sub-class (or owl:sameAs) dc:FileFormat in ontology.
  HP_Filter     = Resource(NS.HP_Filter)
  LP_Filter     = Resource(NS.LP_Filter)
  Notch_Filter  = Resource(NS.Notch_Filter)
  Recording     = Resource(NS.Recording)
  Repository    = Resource(NS.Repository)
  Resolution    = Resource(NS.Resolution)
  Signal        = Resource(NS.Signal)
  Simulation    = Resource(NS.Simulation)
  Source        = Resource(NS.Source)
  Transducer    = Resource(NS.Transducer)
  Type          = Resource(NS.Type)
  UnitOfMeasure = Resource(NS.UnitOfMeasure)

# owl:ObjectProperties:
  annotation    = Resource(NS.annotation)
  filter        = Resource(NS.filter)
  ##format        = Resource(NS.format)  ## Use dc:format (or sub-class...??)
  recording     = Resource(NS.recording)
  repository    = Resource(NS.repository)
  resolution    = Resource(NS.resolution)
  signal        = Resource(NS.signal)
  transducer    = Resource(NS.transducer)
  time          = Resource(NS.time)
  type          = Resource(NS.type)
  units         = Resource(NS.units)

# owl:DataProperties:
  sampleRate    = Resource(NS.rate)
  minFrequency  = Resource(NS.minFrequency)
  maxFrequency  = Resource(NS.maxFrequency)
  minValue      = Resource(NS.minValue)
  maxValue      = Resource(NS.maxValue)
  scale         = Resource(NS.scale)
  offset        = Resource(NS.offset)
  signalcount   = Resource(NS.signalcount)

# owl:Things:
  # Biosignal file formats
  BioSignalML   = Resource(NS.BioSignalML)
  SignalStream  = Resource(NS.SignalStream)
  RAW           = Resource(NS.RAW)
  EDF           = Resource(NS.EDF)
  EDFplus       = Resource(NS.EDFplus)
  FieldML       = Resource(NS.FieldML)
  MFER          = Resource(NS.MFER)
  SCP_ECG       = Resource(NS.SCP_ECG)
  WFDB          = Resource(NS.WFDB)
  SDF           = Resource(NS.SDF)
  HDF5          = Resource(NS.HDF5)
  CLOCK         = Resource(NS.CLOCK)

  # Types of biosignals
  BP            = Resource(NS.BP)
  ECG           = Resource(NS.ECG)
  EEG           = Resource(NS.EEG)


"""
from signal    import Signal
from signalset import SignalSet
from recording import Recording
from data      import TimeSeries, DataError
"""
