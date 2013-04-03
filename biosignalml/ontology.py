"""
Provide access to the BioSignalML ontology.

Generated from file:///Users/dave/biosignalml/ontologies/bsml/2011-04-biosignalml.ttl at Sun Jan  6 22:39:53 2013

Full documentation of the ontology is at http://www.biosignalml.org/ontologies/2011/04/biosignalml
"""

from biosignalml.rdf import Resource, NS as Namespace

class BSML(object):
  URI = "http://www.biosignalml.org/ontologies/2011/04/biosignalml#"
  NS = Namespace(URI)
  prefix = NS.prefix

# owl:Class resources:
  Annotation     = Resource(NS.Annotation)
  '''A general note, comment, or qualitative measure about the whole of,
           or some portion of, a Recording, Signal or Event.'''
  BP_Filter      = Resource(NS.BP_Filter)
  '''A band-pass filter.'''
  Device         = Resource(NS.Device)
  '''The physical device that saved the output of a sensor into a format able to be stored.'''
  Electrode      = Resource(NS.Electrode)
  '''An electrical conductor in contact with non-conducting material, through which
            electrical activity can be measured.'''
  ErrorTag       = Resource(NS.ErrorTag)
  '''A tag to indicate that an annotation relates to some form of error.'''
  Event          = Resource(NS.Event)
  '''Something that has occurred in time, possibly for some duration.'''
  EventType      = Resource(NS.EventType)
  '''Something which is the class or type of an Event.'''
  Filter         = Resource(NS.Filter)
  '''The class of filter that has been applied to a signal during data collection.'''
  HP_Filter      = Resource(NS.HP_Filter)
  '''A high-pass filter.'''
  Instant        = Resource(NS.Instant)
  '''A particular point in time.'''
  Interval       = Resource(NS.Interval)
  '''A period in time.'''
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
  RecordingGraph = Resource(NS.RecordingGraph)
  '''A RDF graph containing Recording metadata, used for managing provenance.'''
  SampleClock    = Resource(NS.SampleClock)
  '''An increasing sequence of sample coordinates.

Several signals may use the same clock.'''

  Segment        = Resource(NS.Segment)

  SemanticTag    = Resource(NS.SemanticTag)
  '''A tag used to classify a resource.'''
  Sensor         = Resource(NS.Sensor)
  '''What actually captured a signal -- an electrode, transducer, etc.'''
  Signal         = Resource(NS.Signal)
  '''A sequence of periodic measurements of some physical quantity, ordered by some sampling
           dimension, normally time. A Signal is part of some Recording.'''
  SignalType     = Resource(NS.SignalType)
  '''The class or type of signal (e.g. EEG, ECG).'''
  Simulation     = Resource(NS.Simulation)
  '''A computer simulation or modelling process that created the Signal or Recording.'''
  Source         = Resource(NS.Source)
  '''The source (i.e. device, simulation, etc) of a Signal or Recording.'''
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
  index          = Resource(NS.index)
  '''The 0-origin position of a signal in a physical recording, or of an event in a sequence of events.'''
  maxFrequency   = Resource(NS.maxFrequency)
  '''The maximum frequency, in Hertz, contained in the signal.'''
  maxValue       = Resource(NS.maxValue)
  '''The maximum value of the signal.'''
  minFrequency   = Resource(NS.minFrequency)
  '''The minimum frequency, in Hertz, contained in the signal.'''
  minValue       = Resource(NS.minValue)
  '''The minimum value of the signal.'''
  offset         = Resource(NS.offset)
  '''The temporal offset, from the beginning of a recording, to a signal's first sample.'''
  period         = Resource(NS.period)
  '''The sampling period, in seconds, of a uniformly sampled signal.'''
  rate           = Resource(NS.rate)
  '''The sampling rate, in Hertz, of a uniformly sampled signal.'''
  resolution     = Resource(NS.resolution)
  '''The resolution, in seconds, of a clock's timing.'''
  time           = Resource(NS.time)
  '''The temporal offset, from the beginning of a recording, to the start of some event.'''

# owl:NamedIndividual resources:
  BP             = Resource(NS.BP)
  ECG            = Resource(NS.ECG)
  EEG            = Resource(NS.EEG)
  ErrorTAG       = Resource(NS.ErrorTAG)

# owl:ObjectProperty resources:
  clock          = Resource(NS.clock)
  '''The sampling coordinates associated with a signal's data values.'''
  dataset        = Resource(NS.dataset)
  '''The location of actual signal data.'''
  eventType      = Resource(NS.eventType)
  '''The class or type of an Event.'''
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
  tag            = Resource(NS.tag)
  '''A semantic tag given to a resource by an annotation.

      Tags are effectively controlled keywords.'''
  units          = Resource(NS.units)
  '''The physical units that are represented by a signal's data values.

Specification of units allows for consistency checking and automatic conversion.'''
