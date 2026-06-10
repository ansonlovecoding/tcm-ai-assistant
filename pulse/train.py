# Training dataset format:
# ppg: (N, 256, 1)
# sbp: (N, 1)
# dbp: (N, 1)
# Training Result
# Epoch 30/30 done  train_loss=8.6882 train_mae=9.17  |  val_loss=10.5998 val_mae=11.09
# time: train=0:01:21  val=0:00:06  epoch=0:01:27  total=0:43:55  eta=0:00:00

import os
import json
import time
from datetime import timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =========================
# Config
# =========================
EPOCHS = 30
BATCH_SIZE = 2048
LR = 1e-3

# =========================
# Drive Paths Configuration
# =========================
# Adjust these paths to your specific folder structure in Google Drive
DRIVE_DATASET_PATH = "/content/drive/MyDrive/dataset"
OUTPUT_DIR = "/content/drive/MyDrive/ppg_model"

# Create model save directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# Dataset
# =========================
class PPGDataset(Dataset):
    def __init__(self, path):
        data = np.load(path)

        self.ppg = data["ppg"].astype(np.float32)
        self.sbp = data["sbp"].astype(np.float32)
        self.dbp = data["dbp"].astype(np.float32)

    def __len__(self):
        return len(self.ppg)

    def __getitem__(self, idx):
        x = self.ppg[idx]

        y = np.array([
            self.sbp[idx][0],
            self.dbp[idx][0]
        ], dtype=np.float32)

        return torch.tensor(x), torch.tensor(y)


# =========================
# Metrics
# =========================
def mae(pred, label):
    return torch.mean(torch.abs(pred - label))


# =========================
# Train
# =========================
def train_one_epoch(epoch, model, loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0
    total_mae = 0.0
    n_batches = len(loader)
    epoch_start = time.time()

    for i, (x, y) in enumerate(loader):
        batch_start = time.time()

        x = x.to(device)
        y = y.to(device)

        pred = model(x)

        loss = criterion(pred, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        batch_loss = loss.item()
        batch_mae = mae(pred, y).item()
        total_loss += batch_loss
        total_mae += batch_mae

        batch_time = time.time() - batch_start
        print(
            f"  [Epoch {epoch+1:>3}/{EPOCHS}] train "
            f"batch {i+1:>4}/{n_batches}  "
            f"loss={batch_loss:.4f}  mae={batch_mae:.4f}  "
            f"batch_time={batch_time*1000:.1f}ms"
        )

    avg_loss = total_loss / n_batches
    avg_mae = total_mae / n_batches
    epoch_time = timedelta(seconds=int(time.time() - epoch_start))
    print(
        f"[Epoch {epoch+1:>3}/{EPOCHS}] train done  "
        f"train_loss={avg_loss:.4f}  train_mae={avg_mae:.4f}  "
        f"time={epoch_time}"
    )

    return avg_loss, avg_mae


# =========================
# Validation
# =========================
def evaluate(epoch, model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    total_mae = 0.0
    n_batches = len(loader)
    epoch_start = time.time()

    preds = []
    labels = []

    with torch.no_grad():
        for i, (x, y) in enumerate(loader):
            batch_start = time.time()

            x = x.to(device)
            y = y.to(device)

            pred = model(x)

            loss = criterion(pred, y)

            batch_loss = loss.item()
            batch_mae = mae(pred, y).item()
            total_loss += batch_loss
            total_mae += batch_mae

            preds.append(pred.cpu())
            labels.append(y.cpu())

            batch_time = time.time() - batch_start
            print(
                f"  [Epoch {epoch+1:>3}/{EPOCHS}] val   "
                f"batch {i+1:>4}/{n_batches}  "
                f"loss={batch_loss:.4f}  mae={batch_mae:.4f}  "
                f"batch_time={batch_time*1000:.1f}ms"
            )

    preds = torch.cat(preds).numpy()
    labels = torch.cat(labels).numpy()

    sbp_true = labels[:, 0]
    dbp_true = labels[:, 1]

    sbp_pred = preds[:, 0]
    dbp_pred = preds[:, 1]

    metrics = {
        "sbp_mae": mean_absolute_error(sbp_true, sbp_pred),
        "dbp_mae": mean_absolute_error(dbp_true, dbp_pred),
        "sbp_rmse": np.sqrt(mean_squared_error(sbp_true, sbp_pred)),
        "dbp_rmse": np.sqrt(mean_squared_error(dbp_true, dbp_pred)),
        "sbp_r2": r2_score(sbp_true, sbp_pred),
        "dbp_r2": r2_score(dbp_true, dbp_pred),
        "overall_mae": (
                               mean_absolute_error(sbp_true, sbp_pred)
                               + mean_absolute_error(dbp_true, dbp_pred)
                       ) / 2,
    }

    avg_loss = total_loss / n_batches
    avg_mae = total_mae / n_batches
    epoch_time = timedelta(seconds=int(time.time() - epoch_start))
    print(
        f"[Epoch {epoch+1:>3}/{EPOCHS}] val   done  "
        f"val_loss={avg_loss:.4f}  val_mae={avg_mae:.4f}  "
        f"sbp_mae={metrics['sbp_mae']:.2f}  dbp_mae={metrics['dbp_mae']:.2f}  "
        f"overall_mae={metrics['overall_mae']:.2f}  time={epoch_time}"
    )

    return (
        avg_loss,
        avg_mae,
        metrics,
        preds,
        labels
    )


def plot_curve(train_values, val_values, ylabel, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(train_values, label="Train")
    plt.plot(val_values, label="Validation")
    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()


def plot_scatter(true, pred, title, filename):
    plt.figure(figsize=(6, 6))
    plt.scatter(true, pred, alpha=0.3)

    mn = min(true.min(), pred.min())
    mx = max(true.max(), pred.max())

    plt.plot([mn, mx], [mn, mx])
    plt.xlabel("True")
    plt.ylabel("Predicted")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()


def plot_bland_altman(true, pred, title, filename):
    mean = (true + pred) / 2
    diff = pred - true

    md = np.mean(diff)
    sd = np.std(diff)

    plt.figure(figsize=(7, 5))
    plt.scatter(mean, diff, alpha=0.3)

    plt.axhline(md)
    plt.axhline(md + 1.96 * sd)
    plt.axhline(md - 1.96 * sd)

    plt.title(title)
    plt.xlabel("Mean")
    plt.ylabel("Difference")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()


def main():
    train_dataset = PPGDataset(os.path.join(DRIVE_DATASET_PATH, "train.npz"))
    val_dataset = PPGDataset(os.path.join(DRIVE_DATASET_PATH, "val.npz"))

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    model = CNN1D().to(device)

    criterion = nn.SmoothL1Loss()
    optimizer = optim.Adam(model.parameters(), lr=LR)

    print(f"Device: {device}")
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")

    history = {
        "train_loss": [],
        "val_loss": [],
        "train_mae": [],
        "val_mae": []
    }

    best_val_loss = float("inf")
    best_metrics = None
    best_preds = None
    best_labels = None

    start_time = time.time()

    for epoch in range(EPOCHS):

        train_loss, train_mae = train_one_epoch(
            epoch,
            model,
            train_loader,
            criterion,
            optimizer,
            device
        )

        val_loss, val_mae, metrics, preds, labels = evaluate(
            epoch,
            model,
            val_loader,
            criterion,
            device
        )

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_mae"].append(train_mae)
        history["val_mae"].append(val_mae)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_metrics = metrics
            best_preds = preds
            best_labels = labels

            torch.save(
                model.state_dict(),
                os.path.join(OUTPUT_DIR, "best_model.pth")
            )

    elapsed = timedelta(seconds=int(time.time() - start_time))

    print(f"Training finished in {elapsed}")
    print(json.dumps(best_metrics, indent=2))

    with open(
            os.path.join(OUTPUT_DIR, "metrics.json"),
            "w"
    ) as f:
        json.dump(best_metrics, f, indent=2)

    plot_curve(
        history["train_loss"],
        history["val_loss"],
        "Loss",
        "loss_curve.png"
    )

    plot_curve(
        history["train_mae"],
        history["val_mae"],
        "MAE",
        "mae_curve.png"
    )

    sbp_true = best_labels[:, 0]
    dbp_true = best_labels[:, 1]

    sbp_pred = best_preds[:, 0]
    dbp_pred = best_preds[:, 1]

    pd.DataFrame({
        "SBP_TRUE": sbp_true,
        "SBP_PRED": sbp_pred,
        "DBP_TRUE": dbp_true,
        "DBP_PRED": dbp_pred
    }).to_csv(
        os.path.join(OUTPUT_DIR, "predictions.csv"),
        index=False
    )

    plot_scatter(
        sbp_true,
        sbp_pred,
        "SBP Scatter",
        "sbp_scatter.png"
    )

    plot_scatter(
        dbp_true,
        dbp_pred,
        "DBP Scatter",
        "dbp_scatter.png"
    )

    plot_bland_altman(
        sbp_true,
        sbp_pred,
        "SBP Bland Altman",
        "sbp_bland_altman.png"
    )

    plot_bland_altman(
        dbp_true,
        dbp_pred,
        "DBP Bland Altman",
        "dbp_bland_altman.png"
    )


if __name__ == "__main__":
    main()
