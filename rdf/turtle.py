######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID$
#
######################################################

class TurtleObject(object):
#==========================

  def __init__(self, uri, Class, statements=[ ]):
  #----------------------------------------------
   self._subject = uri
   self._statements = [ ('a', Class) ]
   self._statements.extend(statements)

  def state(self, property, value):
  #--------------------------------
    self._statements.append((property, value))

  indent = 0

  @classmethod
  def _indent(cls):
  #----------------
    cls.indent += 2

  @classmethod
  def _undent(cls):
  #----------------
    cls.indent -= 2

  def __str__(self):
  #-----------------
    def obj(o):
      return (o._subject if isinstance(o, type(self)) and o._subject
         else ', '.join([obj(v) for v in o]) if isinstance(o, list)
         else o)
    self._indent()
    offset = ' ' * self.indent
    result = [ (self._subject + ' ') if self._subject else '[ ' ] 
    result.append((' ;\n%s' % offset).join(
      ['%s %s' % (p, obj(v)) for p, v in self._statements]
      ))
    result.append(' .' if self._subject else ('\n%s]' % offset)) 
    self._undent()
    return ''.join(result)


if __name__ == '__main__':
#=========================

  print '@prefix tl:    <http://purl.org/NET/c4dm/timeline.owl#RelativeTimeLine> .'
  print '@prefix sleep: <http://www.biosignalml.org/ontologies/2011/05/sleep#> .'
  print '@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .'

  #print '@base <http://base.com/test/> .'

  t = Interval(None, '<tline>', 11.3, 2.5)
  b = TurtleObject('<breath_id>', 'sleep:breath', [ ('tl:time', t),
                                                    ('sleep:centreOfMass', 10.3) ] )
  print b, '\n'

  print TurtleObject('<breath2>', 'sleep:breath', [ ('tl:time', [ b, '"1"^^xsd:double'] ) ]), '\n'

