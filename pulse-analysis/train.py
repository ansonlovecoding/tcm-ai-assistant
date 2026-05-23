# Training dataset format:
# ppg: (N, 256, 1)
# sbp: (N, 1)
# dbp: (N, 1)

import time
from datetime import timedelta

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
from models.cnn1d import CNN1D

# =========================
# 1. Dataset
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
        x = self.ppg[idx]  # (256, 1)

        y = np.array([
            self.sbp[idx][0],
            self.dbp[idx][0]
        ], dtype=np.float32)

        return torch.tensor(x), torch.tensor(y)


# =========================
# 2. Load Data
# =========================
train_dataset = PPGDataset("./dataset/train.npz")
val_dataset   = PPGDataset("./dataset/val.npz")
batch_size = 2048
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

# =========================
# 3. Setup
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNN1D().to(device)

# criterion = nn.MSELoss()
criterion = nn.SmoothL1Loss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

print("=" * 60)
print(f"Device           : {device}")
if device.type == "cuda":
    print(f"GPU              : {torch.cuda.get_device_name(0)}")
print(f"Train samples    : {len(train_dataset):,}  ({len(train_loader)} batches)")
print(f"Val   samples    : {len(val_dataset):,}  ({len(val_loader)} batches)")
print(f"Batch size       : {batch_size}")
print("=" * 60)


# =========================
# 4. Metrics
# =========================
def mae(pred, label):
    return torch.mean(torch.abs(pred - label))


# =========================
# 5. Train
# =========================
def train_one_epoch(epoch):
    model.train()
    total_loss = 0
    total_mae = 0
    num_batches = len(train_loader)
    start = time.time()

    for i, (x, y) in enumerate(train_loader, start=1):
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
        elapsed = time.time() - start
        print(
            f"  [Epoch {epoch+1:>3}/{EPOCHS}] train "
            f"batch {i:>5}/{num_batches}  "
            f"loss={batch_loss:.4f}  mae={batch_mae:.2f}  "
            f"avg_loss={total_loss/i:.4f}  avg_mae={total_mae/i:.2f}  "
            f"batch_time={batch_time*1000:.1f}ms  "
            f"elapsed={timedelta(seconds=int(elapsed))}"
        )

    return total_loss / num_batches, total_mae / num_batches, time.time() - start


# =========================
# 6. Validation
# =========================
def evaluate(epoch):
    model.eval()
    total_loss = 0
    total_mae = 0
    num_batches = len(val_loader)
    start = time.time()

    with torch.no_grad():
        for i, (x, y) in enumerate(val_loader, start=1):
            batch_start = time.time()

            x = x.to(device)
            y = y.to(device)

            pred = model(x)

            loss = criterion(pred, y)

            batch_loss = loss.item()
            batch_mae = mae(pred, y).item()
            total_loss += batch_loss
            total_mae += batch_mae

            batch_time = time.time() - batch_start
            elapsed = time.time() - start
            print(
                f"  [Epoch {epoch+1:>3}/{EPOCHS}] val   "
                f"batch {i:>5}/{num_batches}  "
                f"loss={batch_loss:.4f}  mae={batch_mae:.2f}  "
                f"avg_loss={total_loss/i:.4f}  avg_mae={total_mae/i:.2f}  "
                f"batch_time={batch_time*1000:.1f}ms  "
                f"elapsed={timedelta(seconds=int(elapsed))}"
            )

    return total_loss / num_batches, total_mae / num_batches, time.time() - start


# =========================
# 7. Training Loop
# =========================
best_val_loss = float("inf")

EPOCHS = 30

run_start = time.time()

for epoch in range(EPOCHS):
    print(f"\n----- Epoch {epoch+1}/{EPOCHS} -----")

    train_loss, train_mae, train_time = train_one_epoch(epoch)
    val_loss, val_mae, val_time = evaluate(epoch)

    epoch_time = train_time + val_time
    total_elapsed = time.time() - run_start
    eta = (total_elapsed / (epoch + 1)) * (EPOCHS - epoch - 1)

    print(
        f"Epoch {epoch+1}/{EPOCHS} done  "
        f"train_loss={train_loss:.4f} train_mae={train_mae:.2f}  |  "
        f"val_loss={val_loss:.4f} val_mae={val_mae:.2f}"
    )
    print(
        f"  time: train={timedelta(seconds=int(train_time))}  "
        f"val={timedelta(seconds=int(val_time))}  "
        f"epoch={timedelta(seconds=int(epoch_time))}  "
        f"total={timedelta(seconds=int(total_elapsed))}  "
        f"eta={timedelta(seconds=int(eta))}"
    )

    # save best model
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "best_model.pth")
        print(f"  Saved best model (val_loss={val_loss:.4f}) -> best_model.pth")

print(f"\nTraining finished in {timedelta(seconds=int(time.time() - run_start))}.  Best val_loss={best_val_loss:.4f}")