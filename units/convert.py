import pint

import biosignalml.rdf             as rdf
import biosignalml.rdf.sparqlstore as sparqlstore

from biosignalml.rdf import RDF
UOME_CORE = rdf.NS('http://www.sbpax.org/uome/core.owl#')

UNITS_GRAPH = "http://devel.biosignalml.org/units"

UNIT_PREFIXES = [ rdf.UOME.prefix,
                  "http://www.biosignalml.org/ontologies/examples/unit#"
                ]

def strip_prefix(uri):
#=====================
  for p in UNIT_PREFIXES:
    if uri.startswith(p): return(uri[len(p):])
  raise ValueError("URI doesn't have a standard unit's prefix")  


_UNIT_REGISTRY = pint.UnitRegistry(None)
_Quantity      = _UNIT_REGISTRY.Quantity

_UNIT_REGISTRY.add_unit('Metre',    _Quantity(None, pint.UnitsContainer({'length': 1})))
_UNIT_REGISTRY.add_unit('Kilogram', _Quantity(None, pint.UnitsContainer({'mass': 1})))
_UNIT_REGISTRY.add_unit('Second',   _Quantity(None, pint.UnitsContainer({'time': 1})))
_UNIT_REGISTRY.add_unit('Ampere',   _Quantity(None, pint.UnitsContainer({'current': 1})))
_UNIT_REGISTRY.add_unit('Candela',  _Quantity(None, pint.UnitsContainer({'luminosity': 1})))
_UNIT_REGISTRY.add_unit('Mole',     _Quantity(None, pint.UnitsContainer({'substance': 1})))
_UNIT_REGISTRY.add_unit('Kelvin',   _Quantity(None, pint.UnitsContainer({'temperature': 1})))
_UNIT_REGISTRY.add_unit('Dimensionless', _Quantity(None, pint.UnitsContainer({'dimensionless': 1})))


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
        _UNIT_REGISTRY.add_unit(name, _Quantity(None, None)) # Dimensionless
        unit = _UNIT_REGISTRY[name]
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
          _UNIT_REGISTRY.add_unit(name, self.get_unit(derivation.unit1))
          unit = _UNIT_REGISTRY[name]
        else:
          raise ValueError("Invalid unit's derivation")
      self._cache[uri] = unit
    return unit


if __name__ == '__main__':
#=========================
  
  def test(u):
  #-----------
    print u, '\n  ', repr(store.get_unit(u))

  store = UnitStore(sparqlstore.Virtuoso('http://localhost:8890'), UNITS_GRAPH)
  test('http://www.sbpax.org/uome/list.owl#Centimetre')
  test('http://www.sbpax.org/uome/list.owl#RadianPerSecond')
  test('http://www.sbpax.org/uome/list.owl#RadianPerSecondSquared')
  test('http://www.biosignalml.org/ontologies/examples/unit#MillimetresOfWater')
  test('http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')

  d = store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#DecilitrePerMinute')
  c = store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#CentilitrePerMinute')
  x = d/c
  print repr(x), x.unitless, x.dimensionless, x.magnitude

  r = store.get_unit('http://www.sbpax.org/uome/list.owl#Radian')
  x = d/r
  print repr(x), x.unitless, x.dimensionless, x.magnitude
## Can convert if unitless

  dl = store.get_unit('http://www.sbpax.org/uome/list.owl#Decilitre')
  print repr(dl/d)

  dl = store.get_unit('http://www.biosignalml.org/ontologies/examples/unit#Decilitre')

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
