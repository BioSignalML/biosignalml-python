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

