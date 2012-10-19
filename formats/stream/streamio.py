######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################


import threading, Queue
import logging
import struct
import sys
import numpy as np
import math
from time import sleep


from biosignalml.rdf  import RDF, DCT, Graph, Uri
from biosignalml      import BSML, Recording
from biosignalml.data import TimeSeries

import blockio
from blockio import BLOCK_INFO, BLOCK_DATA, BLOCK_META, BLOCK_EVENT

from samplerate import RateConvertor


# RDF Serialisations:
FORMAT_RDFXML   = 'rdfxml'
FORMAT_TURTLE   = 'turtle'
FORMAT_NTRIPLES = 'ntriples'


class StreamError(Exception):
#===========================#
  pass


# Flag byte fields:
FLAG_TFORMAT = 0x80
FLAG_RATE    = 0x40
FLAG_COUNT   = 0x20
FLAG_FORMAT  = 0x10
FLAG_SOFFSET = 0x08


# in separate module/package??
class Stream(object):
#====================

  def __init__(self, uri=None):
  #----------------------------
    self.uri = uri
    self._infoGraph = Graph()
    self._rdfFormat = FORMAT_TURTLE
    self._sig_uri_to_num = { }
    self._sig_num_to_uri = { }
    self._signalset = None
    #?? self._sigcount = 0

## Access to 'known' metadata attributes (known = defined in BSML
## metadata model. What about (say) dc: attributes? Do they also
## have a bsml: equivalence, established via owl:sameAs ??

  def init_metadata(self, info, include=[], exclude=[]):
  #-----------------------------------------------------
    self._infoGraph.parse_string(info, FORMAT_TURTLE, base=Uri('stream'))
    ## logging.debug('INFO: %s', self._info.serialise('turtle'))  ?????
    if self.uri == None:
      self.uri = self._infoGraph.get_property(Uri('stream'), BSML.recording).uri
      self._rdfFormat = self._infoGraph.get_literal_string(Uri('stream/metadata'), DCT.format)
      ## ****** Does having a sigcount make sense, as number of signals
      ## ****** can change...
      #?? self._sigcount = self._infoGraph.get_literal_integer(Uri('stream'), BSML.signalcount)
#     Info has statements such as:
#      </signal/1>  bsml:signal  <full_URI_of_signal_in_say_a_repository>
      for stmt in self._infoGraph.find_statements((None, BSML.signal, None)):
        if str(stmt.subject.uri).startswith('stream/signal/'):
          try:
            signo = int(str(stmt.subject.uri)[14:])
            if (not (include or exclude)
             or include and signo     in include
             or exclude and signo not in exclude):
              self._sig_uri_to_num[stmt.object.uri] = signo-1
            else:
              self._sig_uri_to_num[stmt.object.uri] = -1
            self._sig_num_to_uri[signo-1] = stmt.object.uri
          except:
            pass
#    for k,v in self._sig_num_to_uri.iteritems(): print k, ':', v
    if self._signalset == None:
      self._signalset = SignalSet.create(self.uri)

##?   def get_count(self):
##?   #-------------------
##?     return self._sigcount

  def signal_uri(self, number):      # 1-origin number
  #----------------------------
    return self._infoGraph.get_resource(Uri('/signal/%d' % number), BSML.signal).uri

  def signalno(self, uri):           # 1-origin number
  #----------------------
    return self._sig_uri_to_num[uri] + 1

  def signalnumbers(self):           # 1-origin list of numbers of selected signals in stream
  #----------------------
    nums = [ n+1 for n in self._sig_uri_to_num.itervalues() if n > -1 ]
    nums.sort()
    return nums

  def serialiseRDF(self, format=None):
  #-----------------------------------
    if not format: format = self._rdfFormat
    return self._signalset.serialise(base=None, format=format)

  def metadata(self):
  #------------------
    return self._signalset

  def signals(self):
  #-----------------
    ## As an iterator? Filtered by include/exclude?
    return self._signalset.signals()  ## Is constructed on the fly...
                                      ## And need to add TimeSeries....

"""
  recording['attribute'] means query(recording.node, <bsml:attribute>, ?o) ???
  (after checking bsml:attribute is defined).

  def __getitem__(self, attribute):
    query(recording.node, '<bsml:%s>' % attribute, ?o)
    return ?o


  def __getitem__(self, property_uri):
    query(recording.node, property_uri, ?o)
    return ?o


  signal[BSML.rate]



""" 


class StreamSource(Stream, threading.Thread):
#============================================

  def __init__(self, source, include=[], exclude=[], **kwds):
  #----------------------------------------------------------
    Stream.__init__(self)
    self._blocksource = blockio.BlockSource(source, self._process)
    threading.Thread.__init__(self, **kwds)
    if include: self._included = set(include)
    else:       self._included = set()
    if exclude: self._excluded = set(exclude)
    else:       self._excluded = set()
    self._resample = { }
    self._signal_nos = [ ]
    self._ttype = { }
    self._rates = { }
    self._count = { }
    self._dtype = { }
    self._scaleoffset = { }
    self._nextstart = { }
    self._metaqueue = Queue.Queue()
    self._dataqueue = Queue.Queue()
    self._signalqueue = Queue.Queue()
    self._blocksource.start()
    self._runstate = 0
    self._seenmeta = False
    self._graph = Graph()
    self.start()
    while not self._seenmeta: sleep(0.1)


  def disable_data(self):
  #----------------------
    self._runstate = 1

  def enable_data(self):
  #---------------------
    self._runstate = 2

  def stop(self):
  #--------------
    self._blocksource.stop()  ## will process(-1, None)
    if self._runstate < 2: self._runstate = -1

  def run(self):
  #-------------
    while self._runstate >= 0:
      if not self._metaqueue.empty():
        k, c = self._metaqueue.get()
        if k == BLOCK_INFO: self._processinfo(c)
        else:               self._processmeta(c)
      if self._runstate == 2 and not self._dataqueue.empty():
        k, c = self._dataqueue.get()
        if   k == -1:
          self._finishdata()
          self._runstate = -1
        elif k == BLOCK_DATA: self._processdata(c)
        else:                 self._processevent(c)
      sleep(0)
    self._blocksource.join()


  def active(self):
  #----------------
    return (self._runstate >= 0
         or not self._dataqueue.empty()
         or not self._signalqueue.empty())


  def _process(self, kind, content):
  #---------------------------------
    ##logging.debug("RECVD '%s': %s", kind, content)
    if   kind in [BLOCK_INFO, BLOCK_META]:  self._metaqueue.put((kind, content))
    elif kind in [BLOCK_DATA, BLOCK_EVENT]: self._dataqueue.put((kind, content))
    elif kind == -1 and content is None:    self._dataqueue.put((-1, None))
    else:                                   raise StreamError("Unknown kind of block: '%c'" % kind)

  def _processinfo(self, content):
  #-------------------------------
    self.init_metadata(content, self._included, self._excluded)

  def _processmeta(self, content):
  #-------------------------------
    if self._signalset:
      g = Model()       ########################
      g.parse_string(content, self._rdfFormat, base=self.uri)
      for stmt in g.as_stream():
####      for stmt in parser.%parse_string_as_stream(
        nbr = self._sig_uri_to_num.get(stmt.subject.uri, None)
        if nbr is None or self.accept_signal(nbr):
          self._graph.add_statement(stmt, context=self._signalset)
      self._graph.sync()
    else:
      raise StreamError("Stream's metadata store has not been initialised")
    self._seenmeta = True
    logging.debug('META: %s', self.serialiseRDF('turtle'))

  def _processdata(self, content):
  #-------------------------------
    blockstart = struct.unpack_from('>d', content, 0)[0]
    (sigcount, pos) = blockio.unpack_number(content, 8)
    if sigcount:
      self._signal_nos = [ ]
      for n in xrange(0, sigcount):
        self._signal_nos.append(struct.unpack_from('>H', content, pos)[0])
        pos += 2
    for s in self._signal_nos:
      flag = struct.unpack_from('>B', content, pos)[0]
      pos += 1
      if flag & FLAG_TFORMAT:
        self._ttype[s] = np.dtype(content[pos: pos+3])
        pos += 3
      if flag & FLAG_RATE:
        self._rates[s] = struct.unpack_from('>f', content, pos)[0]
        pos += 4
      if flag & FLAG_COUNT:
        self._count[s] = struct.unpack_from('>I', content, pos)[0]
        pos += 4
      if flag & FLAG_FORMAT:
        self._dtype[s] = np.dtype(content[pos: pos+3])
        pos += 3
      if flag & FLAG_SOFFSET:
        self._scaleoffset[s] = struct.unpack_from('>dd', content, pos)
        pos += 16
    rates = { }
    times = { }
    for s in self._signal_nos:
      if s in self._rates:
        rate = self._rates[s]
        rates[s] = rate if rate > 0 else 0
        if rate == 0:
          if self.accept_signal(s):
            #### See comment below re dtype
            times[s] = np.frombuffer(content, dtype=self._ttype[s], offset=pos, count=self._count[s])
          pos += self._count[s]*self._ttype[s].length
        elif rate < 0:
          times[s] = times[int(-rate)-1]
    for s in self._signal_nos:
      ##### Want to get as native format regardless of stream's format
      ##### Stream's format is in self._dtype
      if self.accept_signal(s) and s in rates:  # Only if we have timing information for signal
#### and only if we have a signal data handler for this signal...
        data = np.fromstring(content[pos:], dtype=self._dtype[s], count=self._count[s])
#### ????        scaledata = scale * data + offset  ## Do we use, return this??
####    if self._scaleoffset.get(s, None):
####      scaleddata = self._scaleoffset[s][0]*data.astype('float32') + self._scaleoffset[s][1]
####    float32 v's double (= float)  ?????????
#### ????        Esp. when resampling ?????????
        if self._resample.get(s, None):
          if self._rates[s]:
            sigdata = TimeSeries(self._sig_num_to_uri[s], s+1,  # 1-origin
              self._nextstart.get(s, blockstart),
              self._resample[s].rate, self._resample[s].convert(rates[s], data),
              self._scaleoffset.get(s, None))
          else:
            raise StreamError('Can only rate convert a uniformly sampled signal')
        else:
          sigdata = TimeSeries(self._sig_num_to_uri[s], s+1,    # 1-origin
            blockstart,
            rates[s], data,
            self._scaleoffset.get(s, None), times.get(s, None))
        self._nextstart[s] = sigdata.nextstart
        self._signalqueue.put(sigdata)
        ## or call data handler...
      pos += self._count[s]*self._dtype[s].itemsize

  def _finishdata(self):
  #---------------------
    for s in self._signal_nos:
      if self.accept_signal(s) and self._resample.get(s, None):
        if self._rates[s]:
          sigdata = TimeSeries(self._sig_num_to_uri[s], s+1,    # 1-origin
            self._nextstart[s],
            self._resample[s].rate, self._resample[s].finish(),
            self._scaleoffset.get(s, None))
          self._signalqueue.put(sigdata)
        else:
          raise StreamError('Can only rate convert a uniformly sampled signal')


  def _processevent(self, content):
  #--------------------------------
    pass


  def set_sample_rate(self, rate):
  #-------------------------------
    changedrates = []
    for s in self.signals():
      if s.rate != rate:
        changedrates.append(s.uri) 
        self._resample[self._sig_uri_to_num[s.uri]] = RateConvertor(rate)

    ## In fact we now need a new URI (and updated in uri->num
    ## as well as in signalset.signals...

    for stmt in self._graph.as_stream(context=self._signalset):
    ## store --> triplestore
      olduri = stmt.subject.uri
      if olduri in changedrates:
        newuri = Uri(str(olduri) + '?rate=%f' % rate)
        ## Need to get signal id (after ".../recording/uri/signal/"
        ## New id = id + "/rate/100 ?? Or use query ??
        ## Fragment is for time segments
        if newuri not in self._sig_uri_to_num:
          self._sig_uri_to_num[newuri] = self._sig_uri_to_num[olduri]
          self._sig_num_to_uri[self._sig_uri_to_num[olduri]] = newuri
          del self._sig_uri_to_num[olduri]
          self._signalset.del_signal(olduri)
          sig = self._signalset.add_signal(uri=newuri)
          sig.source = olduri
          sig.rate = rate
        ##  ????????????????????????      del triplestore[stmt, self._signalset] ########
        if stmt.predicate not in [BSML.recording, BSML.sampleRate]:
          stmt.subject = Resource(newuri)
          self._graph.add_statement(stmt, context=self._signalset)
    triplestore.sync()



  """
  def include_signals(self, siglist):
  #----------------------------------
    self._included = self._included.union(siglist)
    self._excluded = self._excluded.difference(siglist)

  def exclude_signals(self, siglist):
  #----------------------------------
    self._excluded = self._excluded.union(siglist)
    self._included = self._included.difference(siglist)
  """

  def accept_signal(self, s):
  #--------------------------
    s = s + 1
    return (not self._excluded and not self._included
         or     self._excluded and not self._included and s not in self._excluded
         or                            self._included and s     in self._included)


  def signal_data(self):   ##  ?? Add t/o option ???
  #---------------------
    """
    :return: the next received signal data block.
    :rtype:  :class:`TimeSeries`

    Returns None if no signal data is available.

    """
    if self._runstate == 0: self._runstate = 2  #  Assume caller wants data
    return None if self._signalqueue.empty() else self._signalqueue.get()


"""

How is stream signal-data/events/metadata passed to a user application?

* User polls a 'get_()' function that either waits and returns data and/or returns None
  (maybe have a 'timeout' option).

* We call a user supplied callback function -- either a common one, or one for each class
  of stream information.

* We notify the user that data is available -- callback? User polls? Message passing??
    
  for data)   


"""



def _dtype(dt):
#==============
  return ((dt.byteorder if dt.byteorder != '='   # What about '@' ??
     else ('<' if sys.byteorder == 'little' else '>')) + dt.name[0] + str(dt.itemsize))


class StreamSink(Stream):
#========================
  """
  :param sink: the file object that the stream is written to.
  :param recordingURI: the URI of the stream.
  :type recordingURI: :class:`RDF.Uri`
  :param signalURIs: the URIs of the signals in the stream
  :param blocktime: the minimum size, in seconds, of a data block. A value of 0
      means data is output whenever any signal fragment has a more recent
      start time than what was last buffered to send; a negative value
      means signal data is sent immediately, without buffering.
  """

  def __init__(self, sink, recordingURI, signalURIs, blocktime=1.0):
  #-----------------------------------------------------------------
    Stream.__init__(self, recordingURI)
    self._blocksink = blockio.BlockSink(sink)
    ##self._infoGraph.append((Uri('/stream'),   DCT.version, '1.0')) ## ????????????
    self._infoGraph.append((Uri('stream'),   RDF.type,       BSML.SignalStream))
    self._infoGraph.append((Uri('stream'),   BSML.recording, Uri(recordingURI)))
    self._infoGraph.append((Uri('stream/metadata'), DCT.format,     self._rdfFormat))
##?     self._infoGraph.append_integer((Uri('stream'), BSML.signalcount, len(signalURIs)))

    #info = ['@prefix xsd: <http://www.w3.org/2001/XMLSchema-datatypes#> .',
    #        '<#stream> a <%s> .'      % (str(BSML.SignalStream.uri)),
    #        '<#stream> <%s> <%s> .'   % (str(BSML.recording.uri), str()),
    #        '<#metadata> <%s> "%s" .' % (str(DCT.format.uri), self._rdfFormat),
    #        '<#stream> <%s> "%d"^^xsd:int .' % (str(BSML.signalcount.uri), len(signalURIs)),
    #       ]
## Does sending signal count and signal URIs make sense, given the
## dynamic nature of a stream's content...

    self._lastsignal = len(signalURIs) - 1    
    for n, s in enumerate(signalURIs):
## Is this 'n' the signal id ???
##   YES, and this is how we map signal id to URI
##   So we should check signal id is in range when sending data...
      #info.append('</signal/%d> <%s> <%s> .' % (n+1, str(BSML.signal.uri), str(Uri(s))))
      self._infoGraph.append((Uri('stream/signal/%d' % (n+1)), BSML.signal, Uri(s)))
      self._sig_num_to_uri[n] = s
      self._sig_uri_to_num[s] = n

    self._blocksink.write(BLOCK_INFO, self._infoGraph.serialise(format = FORMAT_TURTLE,
##                                                                base   = Uri(str(recordingURI) + '/'),
                                                                namespaces = {'bsml': BSML.uri}))
    self._blockstart = 0
    self._blocksigs = [ ]
    self._blockdata = { }

    # For data streaming
    self._signal_nos = [ ]
    self._ttype = { }
    self._rates = { }
    self._count = { }
    self._dtype = { }
    self._scaleoffset = { }
    self._blocktime = blocktime


  def send_metadata(self, resource, base):
  #--------------------------------------
    self._blocksink.write(BLOCK_META, resource.serialise(base, format=self._rdfFormat))


  def _writedata(self, blockstart, sigblocks):
  #-------------------------------------------
    """
    :param sigblocks: the signal blocks to write.
    :type  sigblocks: list of :class:`TimeSeries`
    :param float blockstart: start time of this block.

    See :ref:`dataformat` for a description of a data block's layout.

    """
    signos = [self._sig_uri_to_num[s.signal_id] for s in sigblocks]
    ## And what about linked times for irregular sampled signals ????
    ## What if unknown URI ???
    headers = [struct.pack('>d', blockstart)]
    if self._signal_nos != signos:
      headers.append(blockio.packlen(signos))
      for s in signos: headers.append(struct.pack('>H', s))
      self._signal_nos = signos
    else:
      headers.append(blockio.packlen(length=0))
    data = [ ]
    times = [ ]
    for sd in sigblocks:
      signum = self._sig_uri_to_num[sd.signal_id]
      flag = 0
      header = [ ]
      timing = sd.times
      if timing is None:
        rate = sd.rate
      else:
        if isinstance(timing, TimeSeries):  # Signal that has timing
          rate = -self._sig_uri_to_num[timing.signal_id]
          if len(sd) != len(timing):
            raise StreamError("Timing signal has different length")
        else:
          rate = 0
          ttype = _dtype(timing.dtype)
          if self._ttype.get(signum, '') != ttype:
            flag |= FLAG_TFORMAT
            header.append(ttype.ljust(3))
            self._ttype[signum] = ttype
          if len(timing) != len(sd):
            raise StreamError("Timing length doesn't match data")
          times.append(str(timing.data))
      if self._rates.get(signum, '') != rate:
        flag |= FLAG_RATE
        header.append(struct.pack('>f', rate))
        self._rates[signum] = rate
      samples = len(sd)
      if self._count.get(signum, '') != samples:
        flag |= FLAG_COUNT
        header.append(struct.pack('>I', samples))
        self._count[signum] = samples
      dtype = _dtype(sd.data.dtype)
      if self._dtype.get(signum, '') != dtype:
        flag |= FLAG_FORMAT
        header.append(dtype.ljust(3))
        self._dtype[signum] = dtype
      soffset = sd.scaling
      if soffset and self._scaleoffset.get(signum, '') != soffset:
        flag |= FLAG_SOFFSET
        header.append(struct.pack('>dd', *soffset))
        self._scaleoffset[signum] = soffset
      header.insert(0, struct.pack('>B', flag))
      headers.append(''.join(header))
      data.append(str(sd.data.data))
    hdr = ''.join(headers)
    self._blocksink.write(BLOCK_DATA, hdr + ''.join(times) + ''.join(data))


  def _senddata(sigdata):
  #---------------------
    self._writedata(sigdata.start, [sigdata])

  def _sendblock(self):
  #--------------------
    if self._blockdata:
      self._writedata(self._blockstart,
        [self._blockdata[s] for s in self._blocksigs if s in self._blockdata])
    self._blockdata = { }

  def send_signal(self, sigdata):
  #------------------------------
    """
    :param sigdata: the signal data block to send.
    :type  sigdata: :class:`TimeSeries`
    """
    if len(sigdata) <= 0: return
    if sigdata.start < self._blockstart:
      raise StreamError('Signal block starts before last block sent')


    ## is this the place to resample???

    if self._blocktime < 0:
      self._senddata(sigdata)     # Send now
    else:
      offset = sigdata.start - self._blockstart
      if (self._blocktime == 0 and offset > 0      # Send block if signal start is newer
       or self._blocktime > 0 and offset >= self._blocktime): # or block is full
        self._sendblock()
      if (sigdata.signal_id in self._blockdata      # not sent above, so can we join to existing?
        and not self._blockdata[sigdata.signal_id].join(sigdata)):
         self._sendblock()
      if sigdata.signal_id not in self._blockdata:  # Now not in block, so add
        if sigdata.signal_id not in self._blocksigs: self._blocksigs.append(sigdata.signal_id)
        self._blockdata[sigdata.signal_id] = sigdata
        self._blockstart = sigdata.start

  def flush_signals(self):
  #-----------------------
    if self._blocktime >= 0: self._sendblock()


if __name__ == "__main__":
#========================= 

  import sys, time

#  logging.getLogger().setLevel(logging.DEBUG)

  source = StreamSource(sys.stdin)

  sink = StreamSink(sys.stdout, Uri('#recording'), [s.uri for s in source.signals()])

  sink.send_metadata(source.metadata())  ## ??????????????
  while source.active():
    sig = source.signal_data()
    print sig
    sink.send_signal(sig)
  sink.flush_signals()

"""
Sending:

  signal blocks, each with a starttime and either rate or timing
  are sent to output stream.

  options for unbuffered sends (direct sends) ==> signal block immediately output
   or buffered sends (with a max buffer size, in seconds)

    If max buffer size == 0 then flush/send when start of new block to send > last block's
    start time.

  User gives us TimeSeries, we construct DataFrame objects to pass to write_data()


Model:

  blockio sends/receives blocks

  streamio adds meanings to these blocks (I, M, D, E) and uses
  them to transfer state about signals.

  From API viewpoint, stream is holds information about signals that can
  be queried, read and updated.



"""
