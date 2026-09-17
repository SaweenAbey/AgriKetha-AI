import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

# --------------------------------------------------
# PATHS
# --------------------------------------------------
BASE_DATA = r"C:\Users\ASUS\OneDrive\Documents\GitHub\AgriKetha-AI\backend\data"
DATA_PATH = os.path.join(BASE_DATA, "rice_pests")

BATCH_SIZE = 4
TOTAL_EPOCHS = 5
IMAGE_SIZE = 224

# --------------------------------------------------
# DATA AUGMENTATION (Extra flips for pests)
# --------------------------------------------------
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
print("🐛 Training PEST Model...")
dataset = datasets.ImageFolder(DATA_PATH, transform=train_transform)
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
val_dataset.dataset.transform = val_transform

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

print(f"📊 Pest - Train: {len(train_dataset)}, Val: {len(val_dataset)}")
print(f"🏷️ Classes: {dataset.classes}")

# --------------------------------------------------
# MODEL
# --------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1)
num_classes = len(dataset.classes)
model.classifier = nn.Sequential(
    nn.Linear(960, 1280),
    nn.Hardswish(),
    nn.Dropout(0.2),
    nn.Linear(1280, num_classes)
)
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

# ============================================
# 🔥 RESUME CHECKPOINT LOGIC
# ============================================
CHECKPOINT_FILE = "checkpoint_pest.pth"
START_EPOCH = 0
best_acc = 0.0

if os.path.exists(CHECKPOINT_FILE):
    print(f"💾 Found checkpoint! Resuming Pest training...")
    checkpoint = torch.load(CHECKPOINT_FILE, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    START_EPOCH = checkpoint['epoch'] + 1
    best_acc = checkpoint.get('best_acc', 0.0)
    print(f"✅ Resuming from Epoch {START_EPOCH + 1}")
else:
    print("🆕 Starting fresh Pest training.")

# --------------------------------------------------
# TRAINING
# --------------------------------------------------
for epoch in range(START_EPOCH, TOTAL_EPOCHS):
    model.train()
    correct, total = 0, 0
    train_bar = tqdm(train_loader, desc=f"Pest Epoch {epoch+1}/{TOTAL_EPOCHS}")
    for images, labels in train_bar:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        _, pred = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (pred == labels).sum().item()

    # Validation
    model.eval()
    val_correct, val_total = 0, 0
    val_loss = 0.0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            _, pred = torch.max(outputs, 1)
            val_total += labels.size(0)
            val_correct += (pred == labels).sum().item()

    val_acc = val_correct / val_total
    scheduler.step(val_loss / len(val_loader))
    print(f"   Train Acc: {correct/total:.4f}, Val Acc: {val_acc:.4f}")

    # Save best model
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), "best_pest_model.pth")
        with open("pest_classes.txt", "w") as f:
            for cls in dataset.classes:
                f.write(f"Pest_{cls}\n")
        print(f"  ✅ New best pest model saved! (Val Acc: {val_acc:.4f})")

    # ============================================
    # 🔥 SAVE CHECKPOINT (Resumable)
    # ============================================
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_acc': best_acc,
        'val_acc': val_acc,
    }
    torch.save(checkpoint, CHECKPOINT_FILE)
    print(f"  💾 Checkpoint saved for epoch {epoch+1}")

print(f"🏆 Pest Model Complete! Best: {best_acc:.4f}")