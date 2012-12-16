import pint

import biosignalml.rdf             as rdf
import biosignalml.rdf.sparqlstore as sparqlstore

from biosignalml.rdf import RDF
UOME_CORE = rdf.NS('http://www.sbpax.org/uome/core.owl#')

UNITS_GRAPH = "http://devel.biosignalml.org/units"

UNIT_PREFIXES = [ rdf.UOME.prefix,
                  "http://www.biosignalml.org/ontologies/examples/unit#"
                ]

BASE_UNITS = { 'Metre':         'length',
               'Kilogram':      'mass',
               'Second':        'time',
               'Ampere':        'current',
               'Candela':       'luminosity',
               'Mole':          'substance',
               'Kelvin':        'temperature',
               'Dimensionless': 'dimensionless',
             }


def strip_prefix(uri):
#=====================
  for p in UNIT_PREFIXES:
    if uri.startswith(p): return(uri[len(p):])
  raise ValueError("URI doesn't have a standard unit prefix")  


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
    self._registry = pint.UnitRegistry(None)
    for u, t in BASE_UNITS.iteritems():
      self._registry.add_unit(u, self._registry.Quantity(None, pint.UnitsContainer({t: 1})))

  def contains(self, uri):
  #------------------------
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
      name = strip_prefix(uri)
      if not self.contains(uri):
        raise KeyError("URI is not in units' ontologies")
      derivation = self.get_derivation(uri)
      if derivation is None:
        if name not in BASE_UNITS:
          self._registry.add_unit(name, self._registry.Quantity(None, None)) # Dimensionless
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
          self._registry.add_unit(name, self.get_unit(derivation.unit1))
          unit = self._registry[name]
        else:
          raise ValueError("Invalid unit's derivation")
      self._cache[uri] = unit
    return unit



class UnitConversion(object):
#============================

  def __init__(self, store):
  #-------------------------
    self._store = UnitStore(store, UNITS_GRAPH)

  def mapping(self, uri1, uri2):
  #-----------------------------
    ratio = self._store.get_unit(uri1)/self._store.get_unit(uri2)
    if ratio.unitless: return lambda x: x*ratio.magnitude + 0.0   #: (scale, offset)
    else: raise TypeError("Units cannot be converted between")


if __name__ == '__main__':
#=========================
  
  store = UnitConversion(sparqlstore.Virtuoso('http://localhost:8890'))

  def test(u):
  #-----------
    print u, '\n  ', repr(store._store.get_unit(u))

  test('http://www.sbpax.org/uome/list.owl#Centimetre')
  test('http://www.sbpax.org/uome/list.owl#RadianPerSecond')
  test('http://www.sbpax.org/uome/list.owl#RadianPerSecondSquared')
  test('http://www.biosignalml.org/ontologies/examples/unit#MillimetresOfWater')
  test('http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')

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
