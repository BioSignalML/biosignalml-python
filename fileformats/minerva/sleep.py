import RDF


class SLEEP(object):
#==================

  uri = RDF.Uri('http://www.biosignalml.org/ontologies/2009/10/sleep#')
  NS = RDF.NS(str(uri))

# OWL classes:
  SleepStage = NS.SleepStage

# Pre 2007 sleep stages:
  Awake      = NS.Awake
  Stage1     = NS.Stage1
  Stage2     = NS.Stage2
  Stage3     = NS.Stage3
  Delta      = NS.Delta
  REM        = NS.REM

# Stage3 and Delta combined into StageN3 from 2007:
  StageW     = NS.StageW    # Awake
  StageN1    = NS.StageN1   # Stage1
  StageN2    = NS.StageN2   # Stage2
  StageN3    = NS.StageN3   # Stage3 and Delta
  StageR     = NS.StageR    # REM
