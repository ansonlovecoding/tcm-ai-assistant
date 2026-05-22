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
import matplotlib.pyplot as plt

MAT_PATH = "../dataset/Part_1.mat"

f = h5py.File(MAT_PATH, "r")

data = f["Part_1"]

record_ref = data[0][0]

record = np.array(f[record_ref])

ppg = record[:, 0]
abp = record[:, 1]
ecg = record[:, 2]

plt.figure(figsize=(15, 8))

plt.subplot(3, 1, 1)
plt.plot(ppg)
plt.title("PPG")

plt.subplot(3, 1, 2)
plt.plot(abp)
plt.title("ABP")

plt.subplot(3, 1, 3)
plt.plot(ecg)
plt.title("ECG")

plt.tight_layout()
plt.savefig("plot.png")
plt.show()