import torch
import numpy as np
from models.cnn1d import CNN1D
from pulse.mock_ppg import MockPpg


class BloodPressurePredictor:

    def __init__(self, model_path, device=None):

        # choose device
        if device is None:
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        else:
            self.device = device

        # create model
        self.model = CNN1D().to(self.device)

        # load trained weights
        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device)
        )

        # inference mode
        self.model.eval()

    def preprocess(self, ppg):

        """
        ppg:
            numpy array
            shape = (256,)
        """

        # convert float32
        ppg = np.array(ppg, dtype=np.float32)

        # z-score normalization
        ppg = (
                      ppg - np.mean(ppg)
              ) / (np.std(ppg) + 1e-8)

        # (256,) -> (256,1)
        ppg = np.expand_dims(ppg, axis=-1)

        # (256,1) -> (1,256,1)
        # Same shape with the training dataset
        ppg = np.expand_dims(ppg, axis=0)

        return ppg

    def predict(self, ppg):

        """
        return:
            sbp, dbp
        """

        # preprocess
        ppg = self.preprocess(ppg)

        # numpy -> tensor
        x = torch.tensor(
            ppg,
            dtype=torch.float32
        ).to(self.device)

        # inference
        with torch.no_grad():

            pred = self.model(x)

        # tensor -> numpy
        pred = pred.cpu().numpy()[0]

        sbp = float(pred[0])
        dbp = float(pred[1])

        return sbp, dbp

# How to use this predictor
# predictor = BloodPressurePredictor(
#     model_path="best_model.pth"
# )
# ppg = MockPpg().ppg
# sbp, dbp = predictor.predict(ppg)
# print(f"Predicted SBP: {sbp:.2f}")
# print(f"Predicted DBP: {dbp:.2f}")