import numpy as np

from biosignalml.data import Clock, TimeSeries
from biosignalml.formats.hdf5 import HDF5Recording


if __name__ == '__main__':
#=========================

  uri = 'http://biosignalml.org/tests/hdf5/1'
  fname = 'testhdf5_1.bsml'
  f = HDF5Recording.create(uri, fname, replace=True)

  s = f.new_signal(uri + '/signal/1', 'mV', rate=1000)
  s.extend([1, 2, 3, 4, 5, 4, 3, 2, 1])

  f.save_metadata()
  f.close()



  uri = 'http://biosignalml.org/tests/hdf5/2'
  fname = 'testhdf5_2.bsml'
  f = HDF5Recording.create(uri, fname, replace=True)

  clock_uri = uri + '/clock'
  timing = Clock(clock_uri, np.array([1, 2, 3, 4, 5, 6, 7, 8, 9]), units='seconds')

  s = f.new_signal(uri + '/signal/1', 'mV', clock=timing)
  s.extend([1, 2, 3, 4, 5, 4, 3, 2, 1])
  
  f.save_metadata()
  f.close()


  """

  g = HDF5Recording.open('testhdf5.h5')

  g.create_signal('a signal URI', 'mV', data=[1, 2, 3], rate=10)
  
  g.create_signal('2d signal', 'mV', data=[1, 2, 3, 4], shape=(2,), rate=100)

  g.create_signal(['URI1', 'URI2'], ['mA', 'mV'], data=[1, 2, 3, 4], period=0.001)

  g.create_clock('clock URI', times=[1, 2, 3, 4, 5])
  g.create_signal('another signal URI', 'mV', data=[1, 2, 1], clock='clock URI')

  g.create_clock('2d clock', times=[1, 2, 3, 4, 5, 6], shape=(2,))

  g.extend_signal('2d signal', [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ])

  g.extend_clock('clock URI', [ 1, 2, 4, 5, 6, 7, 8, 9, ])
  g.extend_signal('another signal URI', [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ])

  print g.get_metadata()

  g.close()
  """

