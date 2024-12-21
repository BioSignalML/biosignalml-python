import numpy as np

from biosignalml.units import get_units_uri
from biosignalml.formats.hdf5 import HDF5Recording

data = np.linspace(10, 20, 501) + 0.2*np.random.normal(size=501)

uri = 'http://biosignalml.org/recordings/opencor/test'
filename = '/Users/dave/Documents/OpenCOR/recording2.biosignalml'

recording = HDF5Recording.create(uri, filename, replace=True)

signal_uri = uri + '/signal/y'
signal = recording.new_signal(signal_uri, get_units_uri('V'), rate = 100, data=data)

signal.extend(data)

recording.close()
