##from biosignalml,owl import UOME

class UOME(object):

  def __getattribute__(self, attr):
    if attr == 'Millisecond': raise AttributeError(attr)
    return attr



_units_to_UOME = { }


_units = {
  '%':    'Percent',
  'A':    'ampere',
  'degC': 'DegreeCelsius',
  'g':    'gram',
  'J':    'joule',
  'K':    'Kelvin',
  'l':    'litre',
  'm':    'metre',
  's':    'second',
  'V':    'volt',
  'W':    'watt'
  }

_powers = {
  '2': 'Square',
  '3': 'Cubic',
  }
           
           
_prefixes = { 'Y': 'Yotta', 'Z': 'Zetta', 'E': 'Exa',
              'P': 'Peta',  'T': 'Tera',  'G': 'Giga',
              'M': 'Mega',  'K': 'Kilo',  'H': 'Hecto',
              'D': 'Deca',
              'd': 'Deci',  'c': 'Centi', 'm': 'Milli',
              'u': 'Micro', 'n': 'Nano',  'p': 'Pico',
              'f': 'Femto', 'a': 'Atto',  'z': 'Zepto',
              'y': 'Yocto',
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
    return _powers[u[p+1:]] + _name(u[:p])
  except ValueError:
    return _name(u)

def to_UOME(units):
#==================
  uom = UOME()  #####
  try:                   return _units_to_UOME[units]
  except KeyError:       pass
  try:                   return getattr(uom, 'Per'.join([_power(u) for u in units.split('/', 1)]))
  except AttributeError: raise KeyError, "Cannot map units of '%s'" % units

if __name__ == '__main__':
#=========================

  def test(u):
    try:
      print '%s --> %s' % (u, to_UOME(u))
    except Exception, msg:
      print '%s --> %s (%s)' % (u, type(msg), str(msg))


  test('Km')
  test('mm^2')
  test('Mm^3')
  test('ms')
  test('Mm/s')
  test('mg')
  test('deg')
  test('%')
  test('uV')
  test('mV')
  test('degC')


