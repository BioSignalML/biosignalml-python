import sys

outputting = False
for l in sys.stdin:
  if l.startswith('\\chapter'):
    outputting = True
  elif l.startswith('\\renewcommand{\\indexname}'):
    outputting = False
  if outputting:
    sys.stdout.write(l)

