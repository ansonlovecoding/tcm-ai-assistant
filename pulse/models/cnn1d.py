# PPG training dataset is one-dimensional sequential dataset with fixed length(Window Size=256)
# And A 1D Convolutional Neural Network (1D CNN) is a deep learning architecture specifically designed to process sequential, 1D data.
# Implement 3 CNN layers(Conv1d(1,32),Conv1d(32,64),Conv1d(64,128)) for training the model to identify more features

import torch.nn as nn


class CNN1D(nn.Module):

    def __init__(self):

        super().__init__()

        self.feature = nn.Sequential(

            nn.Conv1d(
                in_channels=1,
                out_channels=32,
                kernel_size=5,
                padding=2
            ),
            nn.BatchNorm1d(num_features=32),
            nn.ReLU(),

            nn.MaxPool1d(2),

            nn.Conv1d(
                32,
                64,
                kernel_size=5,
                padding=2
            ),
            nn.BatchNorm1d(num_features=64),
            nn.ReLU(),

            nn.MaxPool1d(2),

            nn.Conv1d(
                64,
                128,
                kernel_size=5,
                padding=2
            ),
            nn.BatchNorm1d(num_features=128),
            nn.ReLU(),

            nn.AdaptiveAvgPool1d(1)
        )

        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )

    def forward(self, x):

        # (B, 256, 1) => (B, 1, 256)
        x = x.permute(0, 2, 1)
        x = self.feature(x)
        x = self.regressor(x)

        return x