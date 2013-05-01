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
Abstract BioSignalML objects.
'''

__all__ = [ 'makelabel' ]


from .ontology   import BSML
from .recording  import Recording
from .signal     import Signal
from .event      import Event
from .segment    import Segment
from .annotation import Annotation


def makelabel(label, suffix):
#============================
  """
  Helper function to generate a meaningful label for sub-properties of resources.

  :param label: The label of some resource.
  :param suffix: A suffix to append to the label.
  :return: A string consisting of the label, a '_', and the suffix.
  """
  return label + '_' + suffix


if __name__ == '__main__':
#=========================

  import logging
  logging.getLogger().setLevel('DEBUG')

  import biosignalml.rdf as rdf

  def print_dict(r):
  #-----------------
    print '{'
    for kv in r.__dict__.iteritems(): print '  %s: %s' % kv
    print '  }'

  def check(instance):
  #-------------------
    g = rdf.Graph()
    instance.save_to_graph(g)
#    print g.serialise(format=rdf.Format.TURTLE)
    copy = instance.__class__.create_from_graph(instance.uri, g)
#    if isinstance(instance, Event):
#      print_dict(instance.about)
#      print_dict(copy.about)
#    print instance.metadata_as_string(rdf.Format.TURTLE)
#    print copy.metadata_as_string(rdf.Format.TURTLE)
    if instance.metadata_as_string(rdf.Format.TURTLE) != copy.metadata_as_string(rdf.Format.TURTLE):
      print "INPUT:", instance.metadata_as_string(rdf.Format.TURTLE)
      print "RESULT:", copy.metadata_as_string(rdf.Format.TURTLE)
      raise AssertionError
    return copy


  r1 = Recording('http://example.org/recording', duration='1806')
#  r1 = 'http://example.org/rec1'
#  print r1.metadata_as_string(rdf.Format.TURTLE)

#  a1 = Annotation.Note('http://example.org/ann1', r1, 'comment', creator='dave')
  e1 = Annotation.Note('http://example.org/event', Segment(r1, r1.interval(1, 0.5)),
     'event',
     creator='dave')
  t1 = Annotation.Tag('http://example.org/tag1', r1, 'tag')
#  print t1.metadata_as_string(rdf.Format.TURTLE)
#  for t in t1.tags: print (str(t))

#  r2 = check(r1)
#  a2 = check(a1)
#  print a2.metadata_as_string(rdf.Format.TURTLE)

  e2 = check(e1)
#  print e2.metadata_as_string(rdf.Format.TURTLE)

#  assert(e2.time == e1.time)

#  t2 = check(t1)
#  print t2.metadata_as_string(rdf.Format.TURTLE)
#  for t in t2.tags: print (str(t))

  ev1 = r1.new_event('http://ex.org/evt1', 'etype', 32.0, 10)
#  print ev1.metadata_as_string(rdf.Format.TURTLE)
  ev2 = check(ev1)

  ev1 = r1.new_event('http://ex.org/evt1', 'etype', 32.0)
#  print ev1.metadata_as_string(rdf.Format.TURTLE)
  ev2 = check(ev1)


