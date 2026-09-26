import copy
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


# ============================================================
# Configuration
# ============================================================

DATASET_DIR = Path(r"C:\Users\ASUS\Downloads\crop_classifier_dataset")
MODEL_OUTPUT = Path("best_crop_classifier.pth")
CLASSES_OUTPUT = Path("crop_classes.txt")

IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_EPOCHS = 8
LEARNING_RATE = 0.0001

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 60)
print("Crop Classifier Training")
print("=" * 60)
print(f"Device: {DEVICE}")
print(f"Dataset: {DATASET_DIR}")


# ============================================================
# Image transformations
# ============================================================

train_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

val_test_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])


# ============================================================
# Load datasets
# ============================================================

train_dataset = datasets.ImageFolder(
    DATASET_DIR / "train",
    transform=train_transforms
)

val_dataset = datasets.ImageFolder(
    DATASET_DIR / "val",
    transform=val_test_transforms
)

test_dataset = datasets.ImageFolder(
    DATASET_DIR / "test",
    transform=val_test_transforms
)

print("\nClasses:")
print(train_dataset.classes)

print("\nDataset sizes:")
print(f"Training:   {len(train_dataset)}")
print(f"Validation: {len(val_dataset)}")
print(f"Testing:    {len(test_dataset)}")


# ============================================================
# Save class names
# ============================================================

with open(CLASSES_OUTPUT, "w", encoding="utf-8") as f:
    for class_name in train_dataset.classes:
        f.write(class_name + "\n")

print(f"\nClasses saved to: {CLASSES_OUTPUT}")


# ============================================================
# Data loaders
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# Load pretrained MobileNetV3-Small
# ============================================================

print("\nLoading MobileNetV3-Small...")

weights = models.MobileNet_V3_Small_Weights.DEFAULT

model = models.mobilenet_v3_small(
    weights=weights
)

# Replace final classifier
in_features = model.classifier[-1].in_features

model.classifier[-1] = nn.Linear(
    in_features,
    len(train_dataset.classes)
)

model = model.to(DEVICE)


# ============================================================
# Loss and optimizer
# ============================================================

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# Training
# ============================================================

best_val_accuracy = 0.0
best_model_weights = copy.deepcopy(model.state_dict())

start_time = time.time()

for epoch in range(NUM_EPOCHS):

    print("\n" + "=" * 60)
    print(
        f"Epoch {epoch + 1}/{NUM_EPOCHS}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    model.train()

    running_loss = 0.0
    running_correct = 0
    running_total = 0

    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        running_correct += (
            predictions == labels
        ).sum().item()

        running_total += labels.size(0)

    train_loss = running_loss / running_total

    train_accuracy = (
        running_correct / running_total
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    model.eval()

    val_loss = 0.0
    val_correct = 0
    val_total = 0

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            loss = criterion(outputs, labels)

            val_loss += (
                loss.item() * images.size(0)
            )

            predictions = outputs.argmax(dim=1)

            val_correct += (
                predictions == labels
            ).sum().item()

            val_total += labels.size(0)

    val_loss /= val_total

    val_accuracy = (
        val_correct / val_total
    )

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Accuracy: {train_accuracy:.4f}"
    )

    print(
        f"Val Loss:   {val_loss:.4f} | "
        f"Val Accuracy: {val_accuracy:.4f}"
    )

    # --------------------------------------------------------
    # Save best model
    # --------------------------------------------------------

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy

        best_model_weights = copy.deepcopy(
            model.state_dict()
        )

        torch.save(
            best_model_weights,
            MODEL_OUTPUT
        )

        print(
            f"✓ New best model saved "
            f"(validation accuracy: "
            f"{val_accuracy:.4f})"
        )


# ============================================================
# Load best model
# ============================================================

model.load_state_dict(best_model_weights)

print("\nBest validation accuracy:")
print(f"{best_val_accuracy:.4f}")


# ============================================================
# Test evaluation
# ============================================================

print("\n" + "=" * 60)
print("Testing")
print("=" * 60)

model.eval()

test_correct = 0
test_total = 0

class_correct = [0] * len(test_dataset.classes)
class_total = [0] * len(test_dataset.classes)

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        outputs = model(images)

        predictions = outputs.argmax(dim=1)

        test_correct += (
            predictions == labels
        ).sum().item()

        test_total += labels.size(0)

        for label, prediction in zip(
            labels,
            predictions
        ):

            label_index = label.item()

            class_total[label_index] += 1

            if label == prediction:
                class_correct[label_index] += 1


test_accuracy = test_correct / test_total

print(
    f"\nOverall Test Accuracy: "
    f"{test_accuracy:.4f}"
)

print("\nClass Accuracy:")

for index, class_name in enumerate(
    test_dataset.classes
):

    accuracy = (
        class_correct[index]
        / class_total[index]
    )

    print(
        f"{class_name}: "
        f"{accuracy:.4f}"
    )


# ============================================================
# Final summary
# ============================================================

elapsed = time.time() - start_time

print("\n" + "=" * 60)
print("Training completed!")
print("=" * 60)

print(f"Best Validation Accuracy: {best_val_accuracy:.4f}")
print(f"Test Accuracy:            {test_accuracy:.4f}")
print(f"Training Time:            {elapsed / 60:.2f} minutes")

print(f"\nModel saved as:")
print(MODEL_OUTPUT.resolve())

print("\nClass file:")
print(CLASSES_OUTPUT.resolve())