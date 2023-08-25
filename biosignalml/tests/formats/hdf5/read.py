from biosignalml.formats.hdf5 import HDF5Recording

filename = '/Users/dave/Documents/OpenCOR/recording2.biosignalml'
rec2 = HDF5Recording.open(filename, readonly=True)

uri = 'http://biosignalml.org/recordings/opencor/test'
signal_uri = uri + '/signal/y'

s = rec2.get_signal(signal_uri)
print(s.uri, ' ', s.rate)

for d in s.read():
  print('  ', d.data)

rec2.close()
