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

import logging

from biosignalml.rdf import Resource, NS

from ontology import UNITS

# Export package class
from convert import UnitConverter

__all__ = [ 'get_units_uri' ]


_direct = {
  'Bpm':    'BeatsPerMinute',
  'bpm':    'BeatsPerMinute',
  'cc':     'CubicCentimetre',
  'pm':     'PerMinute',
  '1/min':  'PerMinute',
  'Lpm':    'LitrePerMinute',
  'lpm':    'LitrePerMinute',
  'mv':     'Millivolt',
  'uV-mrs': 'Microvolt',
  'annotation': 'AnnotationData',
  }

_units = {
  '%':     'Percent',
  'A':     'ampere',
  'deg':   'DegreeOfArc',
  'degC':  'DegreeCelsius',
  'mHg':   'metresOfMercury',
  'mH2O':  'metresOfWater',
  'g':     'gram',
  'J':     'joule',
  'K':     'Kelvin',
  'l':     'litre',
  'L':     'litre',
  'm':     'metre',
  'min':   'minute',
  's':     'second',
  'V':     'volt',
  'W':     'watt',
  'bar':   'bar',
  'BPM':   'BeatsPerMinute',
  'bpm':   'BeatsPerMinute',
  'M':     'molar',
  'mol':   'mole',
  }

_powers_prefix = {
  '2': 'Square',
  '3': 'Cubic',
  }

_powers_suffix = {
  '2': 'Squared',
  '3': 'Cubed',
  }


_prefixes = { 'Y': 'Yotta', 'Z': 'Zetta', 'E': 'Exa',
              'P': 'Peta',  'T': 'Tera',  'G': 'Giga',
              'M': 'Mega',  'K': 'Kilo',  'H': 'Hecto',
              'D': 'Deca',
              'd': 'Deci',  'c': 'Centi', 'm': 'Milli',
              'u': 'Micro', 'n': 'Nano',  'p': 'Pico',
              'f': 'Femto', 'a': 'Atto',  'z': 'Zepto',
              'y': 'Yocto',
              u'\u00b5': 'Micro',
            }


def _upperfirst(s):
#------------------
  return s[0].upper() + s[1:]

def _name(u):
#------------
  try:             return _upperfirst(_units[u])
  except KeyError: return _prefixes[u[0]] + _units[u[1:]]

def _power(u):
#-------------
  try:
    p = u.index('^')
    name = _name(u[:p])
    if name.lower().endswith('second'):
      return name + _powers_suffix[u[p+1:]]
    else:
      return _powers_prefix[u[p+1:]] + name
  except ValueError:
    return _name(u)

def _mult(u):
#------------
  return ''.join([_power(v) for v in u.split('*')])


def get_units_uri(s):
#====================
  """
  Convert an abbreviated unit-of-measure into a URI from a unit's ontology.
  """
  if s:
    try:
      unit = _direct[s]
    except KeyError:
      try: unit = 'Per'.join([_mult(u) for u in s.split('/')])
      except KeyError:
        if s.startswith('per_'): unit = 'Per' + _upperfirst(s[4:])
        else:                    unit = _upperfirst(s)
    resource = getattr(UNITS, unit, None)
    if resource is not None: return resource.uri
    raise ValueError("Unknown units abbreviation: %s" % s)


if __name__ == '__main__':
#=========================

  import sys

  def convert(u):
    try:
      o = get_units_uri(u)
      if o: print '%s --> %s' % (u, o)
      else: print 'Cannot convert: %s' % u
    except Exception, msg:
      print 'Error converting: %s (%s)' % (u, msg)

  for l in sys.stdin:
    for w in l.split():
      convert(w)

  '''
  test('Km')
  test('Kg*m/s^2/W*m')
  test('mm^2')
  test('Mm^3')
  test('ms')
  test('Mm/s')
  test('mg')
  test('deg')
  test('%')
  test('uV')
  test('mV')
  test('bar')
  test('mbar')
  test('degC')
  test('mmHg')
  test('cmH2O')
  test('bpm')
  test('clpm')
  test('')
  test(u'\u00b5V')
  '''
