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

import pint
import pint.unit

import logging

import biosignalml.rdf.sparqlstore as sparqlstore

from biosignalml.rdf import NS, RDF, UOME

__all__ = [ 'UnitConverter' ]


UOME_CORE = NS('http://www.sbpax.org/uome/core.owl#')

'''Graph holding http://www.sbpax.org/uome/core.owl#UnitOfMeasurement resources.'''
UNITS_GRAPH = "http://ontologies.biosignalml.org/units"

UNIT_PREFIXES = [ UOME.prefix,
                  "http://www.biosignalml.org/ontologies/examples/unit#"
                ]

BASE_UNITS = { 'Metre':         '[length]',
               'Kilogram':      '[mass]',
               'Second':        '[time]',
               'Ampere':        '[current]',
               'Candela':       '[luminosity]',
               'Mole':          '[substance]',
               'Kelvin':        '[temperature]',
               'Dimensionless': '[dimensionless]',
             }


def _strip_prefix(uri):
#======================
  for p in UNIT_PREFIXES:
    if uri.startswith(p): return(uri[len(p):])
  raise ValueError("'%s' doesn't have a standard unit prefix" % uri)


class UnitTerm(object):
#======================

  def __init__(self, kind):
  #------------------------
    self.kind = str(kind)

  def set_property(self, p, v):
  #----------------------------
    p = str(p)
    if   p == str(UOME_CORE.withFactor): self.factor = float(v)
    elif p == str(UOME_CORE.withOffset): self.offset = float(v)
    elif p == str(UOME_CORE.withExponent): self.exponent = float(v)
    elif p == str(UOME_CORE.withUnit):  self.unit1 = v
    elif p == str(UOME_CORE.withUnit1): self.unit1 = v
    elif p == str(UOME_CORE.withUnit2): self.unit2 = v


class UnitStore(object):
#=======================
  """

  :param store: The :class:`SparqlStore` containing units-of-measurement definitions.
  :param str graph: The named graph in the store with the definitions.

  """
  def __init__(self, store, graph):
  #--------------------------------
    self._store = store
    self._graph = graph
    self._cache = { }
    self._registry = pint.UnitRegistry(None)   # Start with an empty registry
    for u, t in BASE_UNITS.iteritems():        # and add the base units.
      self._registry.define(pint.unit.UnitDefinition(u, None, (), pint.unit.ScaleConverter(1),
                                                     reference=pint.unit.UnitsContainer({t: 1.0}),
                                                     is_base=True))

  def contains(self, uri):
  #-----------------------
    return self._store.ask("<%s> a core:UnitOfMeasurement" % uri,
      graph=self._graph, prefixes=dict(core="http://www.sbpax.org/uome/core.owl#"))

  def get_derivation(self, uri):
  #-----------------------------
    derivation = None
    saved = [ ]
    for r in self._store.select("?p ?o",
     "<%s> a core:UnitOfMeasurement ; core:derivedBy [ ?p ?o ]" % uri,
     graph=self._graph, prefixes=dict(core="http://www.sbpax.org/uome/core.owl#")):
      p = sparqlstore.get_result_value(r, 'p')
      o = sparqlstore.get_result_value(r, 'o')
      if str(p) == str(RDF.type):
        derivation = UnitTerm(o)
        while len(saved):
          p, o = saved.pop(0)
          derivation.set_property(p, o)
      elif derivation is None:
        saved.append((p, o))
      else:
        derivation.set_property(p, o)
    return derivation

  def get_unit(self, uri):
  #-----------------------
    uri = str(uri)
    unit = self._cache.get(uri)
    if unit is None:
      name = _strip_prefix(uri)
      if not self.contains(uri):
        raise KeyError("'%s' is not defined in units ontologies" % uri)
      derivation = self.get_derivation(uri)
      if derivation is None:
        if name not in BASE_UNITS:
          self._registry.define(pint.unit.UnitDefinition(name, None, (), pint.unit.ScaleConverter(1),  # Dimensionless
                                                         reference=self._registry.Quantity(None, None)))
        unit = self._registry[name]
      else:
        kind = derivation.kind
        if   kind == str(UOME_CORE.ScalingExpression):
          unit = derivation.factor * self.get_unit(derivation.unit1)
        elif kind == str(UOME_CORE.OffsetExpression):
          unit = derivation.offset + self.get_unit(derivation.unit1)
        elif kind == str(UOME_CORE.ExponentialExpression):
          unit = self.get_unit(derivation.unit1)**derivation.exponent
        elif kind == str(UOME_CORE.ProductExpression):
          unit = self.get_unit(derivation.unit1) * self.get_unit(derivation.unit2)
        elif kind == str(UOME_CORE.QuotientExpression):
          unit = self.get_unit(derivation.unit1) / self.get_unit(derivation.unit2)
        elif kind == str(UOME_CORE.EquivalenzExpression):
          self._registry.define(pint.unit.UnitDefinition(name, None, (), pint.unit.ScaleConverter(1),
                                                         reference=self.get_unit(derivation.unit1)))
          unit = self._registry[name]
        else:
          raise ValueError("Invalid unit's derivation")
      self._cache[uri] = unit
    return unit


class UnitConverter(object):
#===========================

  def __init__(self, store):
  #-------------------------
    self._store = UnitStore(store, UNITS_GRAPH)

  def mapping(self, from_units, to_units):
  #---------------------------------------
    """
    Convert between compatible units.

    :return: A function mapping values in `from_units` to `to_units`.
    """
    ratio = self._store.get_unit(from_units)/self._store.get_unit(to_units)
    if ratio.unitless:
      if ratio.magnitude == 1.0: return lambda x: x
      else:                      return lambda x: x*ratio.magnitude + 0.0   #: (scale, offset)
    else:
      raise TypeError("Cannot convert between %s and %s" % (from_units, to_units))


if __name__ == '__main__':
#=========================

  import sys

  logging.getLogger().setLevel(logging.DEBUG)

  store = UnitConverter(sparqlstore.Virtuoso('http://localhost:8890'))

  def test(u):
  #-----------
    print u, '\n  ', repr(store._store.get_unit(u))

  test('http://www.sbpax.org/uome/list.owl#Centimetre')
  test('http://www.sbpax.org/uome/list.owl#RadianPerSecond')

  test('http://www.sbpax.org/uome/list.owl#RadianPerSecondSquared')
  test('http://www.biosignalml.org/ontologies/examples/unit#MillimetresOfWater')
  test('http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')

  #import sys
  #sys.exit()

  d = store._store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#DecilitrePerMinute')
  c = store._store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')
  x = d/c
  print repr(x), x.unitless, x.dimensionless, x.magnitude

  r = store._store.get_unit('http://www.sbpax.org/uome/list.owl#Radian')
  a = store._store.get_unit('http://www.sbpax.org/uome/list.owl#DegreeOfArc')
  x = r/a
  print "Radian/Degree:", repr(x), x.unitless, x.dimensionless, x.magnitude
## Can convert if unitless

  dl = store._store.get_unit('http://www.sbpax.org/uome/list.owl#Decilitre')
  print repr(dl/d)

  try:
    dl = store._store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#Decilitre')
  except Exception, msg:
    print msg

  f = store.mapping('http://www.biosignalml.org/ontologies/examples/unit#DecilitrePerMinute',
                    'http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')
  print f(12)

  f = store.mapping('http://www.sbpax.org/uome/list.owl#Nanomolar',
                    'http://www.sbpax.org/uome/list.owl#Micromolar')
  print '1200 nM =', f(1200), 'uM'

"""


Radian = [] = rad
_UNIT_REGISTRY.add_unit('Radian',   u.Quantity(None, None))

# equiv to dimensionless ==>

uome-list:Radian
    uome-core:derivedBy [
        uome-core:withUnit uome-list:Dimensionless ;
        a uome-core:EquivalenzExpression
    ] ;
uome-list:DegreeOfArc
    uome-core:derivedBy [
        uome-core:withFactor 0.017453292519943295 ;
        uome-core:withUnit uome-list:Radian ;
        a uome-core:ScalingExpression
    ] ;

bit = []
count = []


"""
