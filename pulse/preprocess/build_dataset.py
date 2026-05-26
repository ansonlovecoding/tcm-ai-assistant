# Download the data set from: https://archive.ics.uci.edu/dataset/340/cuff+less+blood+pressure+estimation
# The data set is in matlab's v7.3 mat file, accordingly it should be opened using new versions of matlab or HDF libraries in other environments.(Please refer to the Web for more information about this format)
# This database consist of a cell array of matrices, each cell is one record part.
# In each matrix each row corresponds to one signal channel:
# 1: PPG(Photoplethysmography) signal, FS=125Hz;  photoplethysmography from fingertip
# 2: ABP(Arterial blood pressure) signal, FS=125Hz; invasive arterial blood pressure (mmHg)
# 3: ECG(Electrocardiogram) signal, FS=125Hz; electrocardiogram from channel II
# Data shape: (1, N)
# Record shape: (N, 3)
# Window size: 256, Many models prefer powers of two such as 128, 256, and 512 because they are computationally efficient
# Stride: 128
# Duration of one data sample: 256 / 125Hz = 2.048 Second
# SBP (Systolic Blood Pressure): the max ABP in the window
# DBP (Diastolic Blood Pressure): the min ABP in the window
import os

import h5py
import numpy as np
from sklearn.model_selection import train_test_split
from glob import glob

WINDOW_SIZE = 256
STRIDE = 128

ppgs = []
sbps = []
dbps = []

mat_files = sorted(glob("../dataset/*.mat"))

for mat_file in mat_files:
    print("Processing:", mat_file)
    f = h5py.File(mat_file, "r")
    keys = list(f.keys())
    data_key = keys[1]   # 或手动选择
    data = f[data_key]

    print("total records:", data.shape[0])

    for i in range(data.shape[0]):
        print("Start processing record:", i)
        try:
            record_ref = data[i][0]

            record = np.array(f[record_ref])

            # verify the shape: (N, 3)
            if record.shape[1] != 3:
                continue

            ppg = record[:,0]
            abp = record[:,1]

            length = len(ppg)

            if length < WINDOW_SIZE:
                continue

            # sliding window
            for start in range(0, length - WINDOW_SIZE, STRIDE):

                end = start + WINDOW_SIZE

                ppg_window = ppg[start:end]
                abp_window = abp[start:end]

                # -------------------
                # data filtering
                # -------------------

                if np.isnan(ppg_window).any():
                    continue

                if np.isnan(abp_window).any():
                    continue

                # Check whether the PPG signal is too flat,less than 0.001
                if np.std(ppg_window) < 1e-3:
                    continue

                # -------------------
                # labeling
                # -------------------

                sbp = np.max(abp_window)
                dbp = np.min(abp_window)

                # filtering noise
                if sbp < 50 or sbp > 250:
                    continue

                if dbp < 30 or dbp > 150:
                    continue

                # -------------------
                # Z-score normalization
                # -------------------

                ppg_window = (
                                     ppg_window - np.mean(ppg_window)
                             ) / (np.std(ppg_window) + 1e-8)

                # reshape: (256,) => (256, 1)
                ppg_window = np.expand_dims(ppg_window, axis=-1)

                ppgs.append(ppg_window)
                sbps.append([sbp])
                dbps.append([dbp])

        except Exception as e:
            print("skip:", i, e)

        finally:
            print("Finish processing record:", i)

    f.close()

ppgs = np.array(ppgs, dtype=np.float32)
sbps = np.array(sbps, dtype=np.float32)
dbps = np.array(dbps, dtype=np.float32)

# ppgs shape = (N, 256, 1)
# sbps/dbps shape = (N,1)   # SBP + DBP
print("ppgs shape:", ppgs.shape)
print("sbps shape:", sbps.shape)
print("dbps shape:", dbps.shape)

# split the data for dataset train, val, test
# train 80%, val 10%, test 10%
indices = np.arange(len(ppgs))
train_idx, temp_idx = train_test_split(
    indices,
    test_size=0.2,
    random_state=42
)
val_idx, test_idx = train_test_split(
    temp_idx,
    test_size=0.5,
    random_state=42
)

print(f"train size: {len(train_idx)}")
print(f"val size: {len(val_idx)}")
print(f"test size: {len(test_idx)}")

ppg_train = ppgs[train_idx]
ppg_val   = ppgs[val_idx]
ppg_test  = ppgs[test_idx]

sbp_train = sbps[train_idx]
sbp_val   = sbps[val_idx]
sbp_test  = sbps[test_idx]

dbp_train = dbps[train_idx]
dbp_val   = dbps[val_idx]
dbp_test  = dbps[test_idx]

os.makedirs("../dataset", exist_ok=True)
np.savez("../dataset/train.npz", ppg=ppg_train, sbp=sbp_train, dbp=dbp_train)
np.savez("../dataset/val.npz", ppg=ppg_val, sbp=sbp_val, dbp=dbp_val)
np.savez("../dataset/test.npz", ppg=ppg_test, sbp=sbp_test, dbp=dbp_test)

print("done.")