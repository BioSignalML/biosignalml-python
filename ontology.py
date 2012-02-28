"""
Provide access to the BioSignalML ontology.

Generated from file:///Users/dave/refactor/ontologies/bsml/2011-04-biosignalml.ttl at Wed Feb 29 11:02:10 2012

Full documentation of the ontology is at http://www.biosignalml.org/ontologies/2011/04/biosignalml
"""

from biosignalml.rdf import Uri, Resource, NS as Namespace

class BSML(object):
  uri = Uri("http://www.biosignalml.org/ontologies/2011/04/biosignalml#")
  NS = Namespace("http://www.biosignalml.org/ontologies/2011/04/biosignalml#")

# owl:Class resources:
  Annotation     = Resource(NS.Annotation)
  '''A general note, comment, or qualitative measure about the whole of,
           or some portion of, a Recording, Signal or Event.'''
  BP_Filter      = Resource(NS.BP_Filter)
  '''A band-pass filter.'''
  Dataset        = Resource(NS.Dataset)
  '''A collection of data files or web services that contain Recording or Signal information.'''
  Device         = Resource(NS.Device)
  '''The physical device that saved the output of a sensor into a format able to be stored.'''
  Electrode      = Resource(NS.Electrode)
  '''An electrical conductor in contact with non-conducting material, through which
            electrical activity can be measured.'''
  Event          = Resource(NS.Event)
  '''Something that has occurred in time, possibly for some duration.'''
  Filter         = Resource(NS.Filter)
  '''The class of filter that has been applied to a signal during data collection.'''
  Format         = Resource(NS.Format)
  '''The particular storage format used to encode a Recording (e.g. EDF+, WFDB, SCP-ECG, MFER).'''
  HP_Filter      = Resource(NS.HP_Filter)
  '''A high-pass filter.'''
  LP_Filter      = Resource(NS.LP_Filter)
  '''A low-pass filter.'''
  Notch_Filter   = Resource(NS.Notch_Filter)
  '''A notch (blocking) filter.'''
  Process        = Resource(NS.Process)
  '''Some method or algorithm applied to one or more Signals in order to derive
           information. The result could vary along a sampling dimension and be considered
           as a Signal.'''
  Recording      = Resource(NS.Recording)
  '''A collection of Signals held as a named entity, all pertaining to one thing
          (the subject) and which have been recorded in the same session.'''
  SampleClock    = Resource(NS.SampleClock)
  '''An increasing sequence of sample coordinates.

Several signals may use the same clock.'''
  Sensor         = Resource(NS.Sensor)
  '''What actually captured a signal -- an electrode, transducer, etc.'''
  Signal         = Resource(NS.Signal)
  '''A sequence of periodic measurements of some quantity, ordered by some sampling
           dimension, normally time. A Signal is part of some Recording.'''
  SignalType     = Resource(NS.SignalType)
  '''The class or type of signal (e.g. EEG, ECG).'''
  Simulation     = Resource(NS.Simulation)
  '''A computer simulation or modelling process that created the Signal or Recording.'''
  Source         = Resource(NS.Source)
  '''The source (i.e. file, device, simulation, etc) of a Signal or Recording.'''
  TemporalEntity = Resource(NS.TemporalEntity)
  '''Some measurement of time, either as a particular point in time or as some interval.'''
  Transducer     = Resource(NS.Transducer)
  '''A device that converts a measurable quantity into an electrical signal
           (e.g. thermistor, pressure sensor, strain gauge).'''
  UniformSignal  = Resource(NS.UniformSignal)
  '''A signal that has been sampled at a constant rate.'''
  UnitOfMeasure  = Resource(NS.UnitOfMeasure)
  '''The class used to represent the types of measurement units used by signals.

Measurement units would normally be entities in a specialised units of measure ontology.'''

# owl:DatatypeProperty resources:
  dataBits       = Resource(NS.dataBits)
  '''The binary-bit resolution of the analogue-to-digital convertor or
        sampling device used to digitise the signal.'''
  maxFrequency   = Resource(NS.maxFrequency)
  '''The maximum frequency, in Hertz, contained in the signal.'''
  maxValue       = Resource(NS.maxValue)
  '''The maximum value of the signal.'''
  minFrequency   = Resource(NS.minFrequency)
  '''The minimum frequency, in Hertz, contained in the signal.'''
  minValue       = Resource(NS.minValue)
  '''The minimum value of the signal.'''
  period         = Resource(NS.period)
  '''The sampling period, in seconds, of a uniformly sampled signal.'''
  rate           = Resource(NS.rate)
  '''The sampling rate, in Hertz, of a uniformly sampled signal.'''

# owl:NamedIndividual resources:
  BP             = Resource(NS.BP)
  BioSignalML    = Resource(NS.BioSignalML)
  ECG            = Resource(NS.ECG)
  EDF            = Resource(NS.EDF)
  EDFplus        = Resource(NS.EDFplus)
  EEG            = Resource(NS.EEG)
  FieldML        = Resource(NS.FieldML)
  MFER           = Resource(NS.MFER)
  RAW            = Resource(NS.RAW)
  '''Raw, binary data with unknown format.'''
  SCP_ECG        = Resource(NS.SCP_ECG)
  SDF            = Resource(NS.SDF)
  WFDB           = Resource(NS.WFDB)

# owl:ObjectProperty resources:
  clock          = Resource(NS.clock)
  '''The sampling coordinates aassociated with a signal's data values.'''
  format         = Resource(NS.format)
  '''The format used to hold the recording.'''
  preFilter      = Resource(NS.preFilter)
  '''Pre-filtering applied to a signal as part of collection.'''
  recording      = Resource(NS.recording)
  '''The Recording a Signal is part of.'''
  sensor         = Resource(NS.sensor)
  '''What was used to collect or derive an electrical signal'''
  signalType     = Resource(NS.signalType)
  '''A signal's generic type.'''
  source         = Resource(NS.source)
  '''The source of a Recording or Signal.'''
  units          = Resource(NS.units)
  '''The physical units that are represented by a signal's data values.

Specification of units allows for consistency checking and automatic conversion.'''
