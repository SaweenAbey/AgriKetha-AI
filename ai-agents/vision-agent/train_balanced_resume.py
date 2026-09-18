import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split, ConcatDataset
from tqdm import tqdm
import numpy as np
from sklearn.utils.class_weight import compute_class_weight

# --------------------------------------------------
# 1. PATHS
# --------------------------------------------------
BASE_DATA = r"C:\Users\ASUS\OneDrive\Documents\GitHub\AgriKetha-AI\backend\data"

DATA_PATHS = {
    "disease": os.path.join(BASE_DATA, "rice_diseases"),
    "nutrient": os.path.join(BASE_DATA, "rice_nutrition"),
    "pest": os.path.join(BASE_DATA, "rice_pests")
}

PREFIX_MAP = {
    "disease": "Disease_",
    "nutrient": "Nutrition_",
    "pest": "Pest_"
}

BATCH_SIZE = 16
TOTAL_EPOCHS = 15
IMAGE_SIZE = 224

# --------------------------------------------------
# 2. DATA AUGMENTATION
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
# 3. LOAD PICTURES
# --------------------------------------------------
print("📥 Loading Rice Datasets for Balanced Training...")
datasets_list = []
combined_class_names = []

for key, path in DATA_PATHS.items():
    if os.path.exists(path):
        temp_dataset = datasets.ImageFolder(root=path, transform=train_transform)
        prefix = PREFIX_MAP.get(key, "")
        prefixed_classes = [f"{prefix}{cls}" for cls in temp_dataset.classes]
        combined_class_names.extend(prefixed_classes)
        
        dataset = datasets.ImageFolder(root=path, transform=train_transform)
        datasets_list.append(dataset)
        print(f"  ✅ {key.upper()}: {len(dataset)} images, {len(dataset.classes)} classes")
    else:
        print(f"  ❌ ERROR: Folder not found at {path}")

combined_dataset = ConcatDataset(datasets_list)

# Split into Train (80%) and Validation (20%)
train_size = int(0.8 * len(combined_dataset))
val_size = len(combined_dataset) - train_size
train_dataset, val_dataset = random_split(combined_dataset, [train_size, val_size])
val_dataset.dataset.transform = val_transform

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

print(f"📈 Training: {len(train_dataset)} images")
print(f"📉 Validation: {len(val_dataset)} images")
print(f"🏷️ Total Classes: {len(combined_class_names)}")

# --------------------------------------------------
# 4. 🔥 FIXED: CLASS WEIGHTS (GUARANTEED TO WORK)
# --------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"💻 Using device: {device}")

# ✅ SAFE METHOD: Extract labels directly from the training dataset
print("📊 Calculating class weights...")
train_labels = []
for idx in train_dataset.indices:
    train_labels.append(combined_dataset[idx][1])

# Calculate balanced weights using sklearn
classes = np.unique(train_labels)
weights = compute_class_weight('balanced', classes=classes, y=train_labels)

# Create full weight tensor for ALL classes
class_weights = torch.ones(len(combined_class_names), dtype=torch.float).to(device)
for idx, class_id in enumerate(classes):
    class_weights[class_id] = weights[idx]

print(f"\n⚖️ Class Weights (Higher = More Attention):")
for i, weight in enumerate(class_weights):
    print(f"   {combined_class_names[i]}: {weight:.2f}")

# --------------------------------------------------
# 5. MODEL
# --------------------------------------------------
model = models.mobilenet_v3_large(pretrained=True)
num_classes = len(combined_class_names)
model.classifier = nn.Sequential(
    nn.Linear(960, 1280),
    nn.Hardswish(),
    nn.Dropout(0.2),
    nn.Linear(1280, num_classes)
)
model = model.to(device)

# 🔥 Use class weights
criterion = nn.CrossEntropyLoss(weight=class_weights)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

# --------------------------------------------------
# 6. CHECKPOINT (RESUME SUPPORT)
# --------------------------------------------------
CHECKPOINT_FILE = "checkpoint_balanced.pth"
START_EPOCH = 0
best_val_acc = 0.0

if os.path.exists(CHECKPOINT_FILE):
    print(f"\n💾 Found checkpoint! Resuming training...")
    checkpoint = torch.load(CHECKPOINT_FILE, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    START_EPOCH = checkpoint['epoch'] + 1
    best_val_acc = checkpoint.get('best_val_acc', 0.0)
    print(f"✅ Resuming from Epoch {START_EPOCH + 1}")
else:
    print("\n🆕 No checkpoint found. Starting fresh training.")

# --------------------------------------------------
# 7. TRAINING LOOP (WITH BEAUTIFUL PROGRESS BARS!)
# --------------------------------------------------
print(f"\n🚀 Starting Balanced Training...\n")

for epoch in range(START_EPOCH, TOTAL_EPOCHS):
    # --- Training ---
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{TOTAL_EPOCHS} Training", ncols=100)
    for images, labels in train_bar:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        train_bar.set_postfix(loss=f"{running_loss/len(train_loader):.4f}")

    train_acc = correct / total
    avg_loss = running_loss / len(train_loader)

    # --- Validation ---
    model.eval()
    val_correct = 0
    val_total = 0
    val_loss = 0.0
    
    val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{TOTAL_EPOCHS} Validation", ncols=100)
    with torch.no_grad():
        for images, labels in val_bar:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_acc = val_correct / val_total
    avg_val_loss = val_loss / len(val_loader)
    scheduler.step(avg_val_loss)

    print(f"\n📊 Epoch {epoch+1}/{TOTAL_EPOCHS} - Loss: {avg_loss:.4f}, Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}\n")

    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), "best_rice_balanced_model.pth")
        with open("class_names.txt", "w") as f:
            for name in combined_class_names:
                f.write(name + "\n")
        print(f"  ✅ New best model saved! (Val Acc: {val_acc:.4f})\n")

    # Save checkpoint
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_val_acc': best_val_acc,
        'val_acc': val_acc,
    }
    torch.save(checkpoint, CHECKPOINT_FILE)
    print(f"  💾 Checkpoint saved for epoch {epoch+1}\n")

print(f"\n🏆 Balanced Training Complete! Best Accuracy: {best_val_acc:.4f}")
print("✅ Model saved as 'best_rice_balanced_model.pth'")