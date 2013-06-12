"""
Provide access to the BioSignalML ontology.

Generated from file:///Users/dave/biosignalml/workspace/ontologies/bsml/2011-04-biosignalml.ttl at 11:11:05 Wed 12 Jun 2013

Full documentation of the ontology is at http://www.biosignalml.org/ontologies/2011/04/biosignalml
"""

from biosignalml.rdf import Resource, NS as Namespace

__all__ = [ "VERSION", "BSML" ]


VERSION = "0.93.5"

class BSML(object):
  """
  RDF resources for each item in the BioSignalML ontology.
  """
  URI = "http://www.biosignalml.org/ontologies/2011/04/biosignalml#"
  NS = Namespace(URI)
  prefix = NS.prefix

# owl:Class resources:
  Annotation     = Resource(NS.Annotation)
  """**owl:Class**: A general note, comment, or qualitative measure about the whole of,
           or some portion of, a Recording, Signal or Event."""
  BP_Filter      = Resource(NS.BP_Filter)
  """**owl:Class**: A band-pass filter."""
  Device         = Resource(NS.Device)
  """**owl:Class**: A physical device that converts the output of a sensor into a format able to be stored."""
  Electrode      = Resource(NS.Electrode)
  """**owl:Class**: An electrical conductor in contact with non-conducting material, through which
            electrical activity can be measured."""
  ErrorTag       = Resource(NS.ErrorTag)
  """**owl:Class**: A tag to indicate that an annotation relates to some form of error."""
  Event          = Resource(NS.Event)
  """**owl:Class**: Something that has occurred in time, possibly for some duration."""
  EventType      = Resource(NS.EventType)
  """**owl:Class**: Something which is the class or type of an Event."""
  Filter         = Resource(NS.Filter)
  """**owl:Class**: The class of filter that has been applied to a signal during data collection."""
  HP_Filter      = Resource(NS.HP_Filter)
  """**owl:Class**: A high-pass filter."""
  Instant        = Resource(NS.Instant)
  """**owl:Class**: A particular point in time."""
  Interval       = Resource(NS.Interval)
  """**owl:Class**: A period in time."""
  LP_Filter      = Resource(NS.LP_Filter)
  """**owl:Class**: A low-pass filter."""
  Notch_Filter   = Resource(NS.Notch_Filter)
  """**owl:Class**: A notch (blocking) filter."""
  Recording      = Resource(NS.Recording)
  """**owl:Class**: A collection of Signals held as a named entity, all pertaining to one thing
          (the subject) and which have been recorded in the same session."""
  RecordingGraph = Resource(NS.RecordingGraph)
  """**owl:Class**: A RDF graph containing Recording metadata, used for managing provenance."""
  SampleClock    = Resource(NS.SampleClock)
  """**owl:Class**: An increasing sequence of sample coordinates.

Several signals may use the same clock."""
  Segment        = Resource(NS.Segment)
  """**owl:Class**: A portion of a Signal or Recording, defined by restricting samples to some
           interval in the sampling dimension."""
  SemanticTag    = Resource(NS.SemanticTag)
  """**owl:Class**: A tag used to classify a resource."""
  Sensor         = Resource(NS.Sensor)
  """**owl:Class**: What actually captured a signal -- an electrode, transducer, etc."""
  Signal         = Resource(NS.Signal)
  """**owl:Class**: A sequence of periodic measurements of some physical quantity, ordered by some sampling
           dimension, normally time. A Signal is part of some Recording."""
  SignalType     = Resource(NS.SignalType)
  """**owl:Class**: The class or type of signal (e.g. EEG, ECG)."""
  Simulation     = Resource(NS.Simulation)
  """**owl:Class**: A computer simulation or modelling process that created the Signal or Recording."""
  Source         = Resource(NS.Source)
  """**owl:Class**: The source (i.e. device, simulation, etc) of a Signal or Recording."""
  TemporalEntity = Resource(NS.TemporalEntity)
  """**owl:Class**: Some measurement of time, either a particular point in time or some interval."""
  Transducer     = Resource(NS.Transducer)
  """**owl:Class**: A device that converts a measurable quantity into an electrical signal
           (e.g. thermistor, pressure sensor, strain gauge)."""
  UniformSignal  = Resource(NS.UniformSignal)
  """**owl:Class**: A signal that has been sampled at a constant rate."""
  UnitOfMeasure  = Resource(NS.UnitOfMeasure)
  """**owl:Class**: The class used to represent the types of measurement units used by signals.

Measurement units would normally be entities in a specialised units of measure ontology."""

# owl:DatatypeProperty resources:
  dataBits       = Resource(NS.dataBits)
  """**owl:DatatypeProperty**: The binary-bit resolution of the analogue-to-digital convertor or
        sampling device used to digitise the signal."""
  filterFrequency = Resource(NS.filterFrequency)
  """**owl:DatatypeProperty**: The cutoff frequency, in Hertz, of a filter."""
  index          = Resource(NS.index)
  """**owl:DatatypeProperty**: The 0-origin position of a signal in a physical recording."""
  maxFrequency   = Resource(NS.maxFrequency)
  """**owl:DatatypeProperty**: The maximum frequency, in Hertz, contained in the signal."""
  maxValue       = Resource(NS.maxValue)
  """**owl:DatatypeProperty**: The maximum value of the signal."""
  minFrequency   = Resource(NS.minFrequency)
  """**owl:DatatypeProperty**: The minimum frequency, in Hertz, contained in the signal."""
  minValue       = Resource(NS.minValue)
  """**owl:DatatypeProperty**: The minimum value of the signal."""
  offset         = Resource(NS.offset)
  """**owl:DatatypeProperty**: The temporal offset, from the beginning of a recording, to a signal's first sample."""
  period         = Resource(NS.period)
  """**owl:DatatypeProperty**: The sampling period, in seconds, of a uniformly sampled signal."""
  rate           = Resource(NS.rate)
  """**owl:DatatypeProperty**: The sampling rate, in Hertz, of a uniformly sampled signal."""
  resolution     = Resource(NS.resolution)
  """**owl:DatatypeProperty**: The resolution, in seconds, of a clock's timing."""

# owl:NamedIndividual resources:
  BP             = Resource(NS.BP)
  """**owl:NamedIndividual**: Blood Pressure"""
  ECG            = Resource(NS.ECG)
  """**owl:NamedIndividual**: Electrocardiogram"""
  EEG            = Resource(NS.EEG)
  """**owl:NamedIndividual**: Electroencephalogram"""
  ErrorTAG       = Resource(NS.ErrorTAG)
  """**owl:NamedIndividual**: Error TAG"""

# owl:ObjectProperty resources:
  clock          = Resource(NS.clock)
  """**owl:ObjectProperty**: The sampling coordinates associated with a signal's data values."""
  dataset        = Resource(NS.dataset)
  """**owl:ObjectProperty**: The location of actual data, in a format suitable for computer processing."""
  eventType      = Resource(NS.eventType)
  """**owl:ObjectProperty**: The class or type of an Event."""
  preFilter      = Resource(NS.preFilter)
  """**owl:ObjectProperty**: Pre-filtering applied to a signal as part of collection."""
  recording      = Resource(NS.recording)
  """**owl:ObjectProperty**: The Recording a Signal is part of."""
  sensor         = Resource(NS.sensor)
  """**owl:ObjectProperty**: What was used to collect or derive an electrical signal."""
  signalType     = Resource(NS.signalType)
  """**owl:ObjectProperty**: A signal's generic type."""
  tag            = Resource(NS.tag)
  """**owl:ObjectProperty**: A semantic tag given to a resource by an annotation.

Tags are effectively controlled keywords."""
  time           = Resource(NS.time)
  """**owl:ObjectProperty**: An instant or interval associated with a resource."""
  uncertainty    = Resource(NS.uncertainty)
  """**owl:ObjectProperty**: A resource describing the measurement uncertainty associated with a Recording,
           Signal, or Segment."""
  units          = Resource(NS.units)
  """**owl:ObjectProperty**: The physical units that are represented by a signal's data values.

Specification of units allows for consistency checking and automatic conversion."""
