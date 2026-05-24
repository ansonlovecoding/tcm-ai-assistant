# Download the data set from: https://archive.ics.uci.edu/dataset/340/cuff+less+blood+pressure+estimation
# The data set is in matlab's v7.3 mat file, accordingly it should be opened using new versions of matlab or HDF libraries in other environments.(Please refer to the Web for more information about this format)
# This database consist of a cell array of matrices, each cell is one record part.
# In each matrix each row corresponds to one signal channel:
# 1: PPG signal, FS=125Hz;  photoplethysmograph from fingertip
# 2: ABP signal, FS=125Hz; invasive arterial blood pressure (mmHg)
# 3: ECG signal, FS=125Hz; electrocardiogram from channel II
# Data shape: (1, N)
# Record shape: (N, 3)

import h5py
import numpy as np

MAT_PATH = "../dataset/Part_1.mat"

f = h5py.File(MAT_PATH, "r")
data = f["Part_1"]
print(f"data shape: {data.shape}")

# check the first record
hz = 125
record_ref = data[0][0]
record = np.array(f[record_ref])
length = len(record[:, 0])
seconds = length / hz

print(f"record shape: {record.shape}")
print(f"record duration: {seconds} seconds")

print(f"""
rows:
0 -> PPG: {record[:, 0]}
1 -> ABP: {record[:, 1]}
2 -> ECG: {record[:, 2]}
""")
