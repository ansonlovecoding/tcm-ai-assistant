from pyclbr import Class

import numpy as np
import matplotlib.pyplot as plt

class MockPpg:
    def __init__(self):
        # fixed seed
        np.random.seed(42)

        # window size
        N = 256

        # time axis
        t = np.linspace(0, 4, N)

        # simulate heartbeat waveform
        ppg = (
                0.6 * np.sin(2 * np.pi * 1.2 * t) +      # main pulse
                0.2 * np.sin(2 * np.pi * 2.4 * t) +      # harmonic
                0.05 * np.random.randn(N)                # noise
        )

        # normalize
        ppg = (ppg - np.mean(ppg)) / np.std(ppg)

        # shape: (256,1)
        self.ppg = ppg

ppgMock = MockPpg()
print("shape:", ppgMock.ppg.shape)
print(ppgMock.ppg[:10])

# plot
plt.plot(ppgMock.ppg)
plt.title("Mock PPG Signal")
plt.xlabel("Time")
plt.ylabel("Amplitude")
plt.show()