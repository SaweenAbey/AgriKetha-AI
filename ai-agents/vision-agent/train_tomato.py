import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split, Subset
from sklearn.utils.class_weight import compute_class_weight
from tqdm import tqdm
import numpy as np


# ============================================================
# 1. SETTINGS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "Tomato Leaf Disease"
)

TRAIN_DIR = os.path.join(DATA_DIR, "train")
TEST_DIR = os.path.join(DATA_DIR, "test")

IMAGE_SIZE = 224

# CPU-friendly settings
BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 0.0005

VALIDATION_SPLIT = 0.20

MODEL_OUTPUT = os.path.join(
    BASE_DIR,
    "best_tomato_model.pth"
)

CLASS_OUTPUT = os.path.join(
    BASE_DIR,
    "tomato_classes.txt"
)


# ============================================================
# 2. DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("TOMATO DISEASE + PEST MODEL TRAINING")
print("=" * 60)

print(f"Device: {device}")

if device.type == "cpu":
    print("Running on CPU.")
    print("CPU-friendly transfer learning mode is enabled.")


# ============================================================
# 3. DATA TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(
        brightness=0.3,
        contrast=0.3,
        saturation=0.3
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])


validation_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])


# ============================================================
# 4. CHECK DATASET
# ============================================================

if not os.path.exists(TRAIN_DIR):
    raise FileNotFoundError(
        f"Training directory not found:\n{TRAIN_DIR}"
    )

if not os.path.exists(TEST_DIR):
    raise FileNotFoundError(
        f"Test directory not found:\n{TEST_DIR}"
    )

print("\nDataset location:")
print(DATA_DIR)


# ============================================================
# 5. LOAD TRAINING DATA
# ============================================================

print("\nLoading tomato training dataset...")

full_dataset = datasets.ImageFolder(
    root=TRAIN_DIR,
    transform=train_transform
)

class_names = full_dataset.classes
num_classes = len(class_names)

print(f"\nNumber of classes: {num_classes}")

print("Classes:")

for i, class_name in enumerate(class_names):
    print(f"  {i}: {class_name}")

print(
    f"\nTotal training images: "
    f"{len(full_dataset)}"
)


# ============================================================
# 6. SAVE CLASS NAMES
# ============================================================

with open(
    CLASS_OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    for class_name in class_names:
        f.write(class_name + "\n")

print("\nClass names saved to:")
print(CLASS_OUTPUT)


# ============================================================
# 7. TRAIN / VALIDATION SPLIT
# ============================================================

validation_size = int(
    len(full_dataset) * VALIDATION_SPLIT
)

train_size = (
    len(full_dataset) -
    validation_size
)

generator = torch.Generator().manual_seed(42)

train_dataset, validation_dataset = random_split(
    full_dataset,
    [train_size, validation_size],
    generator=generator
)

print("\nDataset split:")
print(
    f"  Training:   {len(train_dataset)}"
)
print(
    f"  Validation: {len(validation_dataset)}"
)


# ============================================================
# 8. VALIDATION DATASET
# ============================================================

validation_base_dataset = datasets.ImageFolder(
    root=TRAIN_DIR,
    transform=validation_transform
)

validation_dataset = Subset(
    validation_base_dataset,
    validation_dataset.indices
)


# ============================================================
# 9. DATA LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# 10. CALCULATE CLASS WEIGHTS
# ============================================================

print("\nCalculating class weights...")

all_labels = np.array(
    full_dataset.targets
)

train_indices = np.array(
    train_dataset.indices
)

train_labels = all_labels[
    train_indices
]

class_ids = np.arange(
    num_classes
)

class_weights_np = compute_class_weight(
    class_weight="balanced",
    classes=class_ids,
    y=train_labels
)

class_weights = torch.tensor(
    class_weights_np,
    dtype=torch.float32
).to(device)

print("\nClass weights:")

for i, weight in enumerate(class_weights):

    print(
        f"  {class_names[i]}: "
        f"{weight.item():.3f}"
    )


# ============================================================
# 11. CREATE MOBILENETV3 LARGE
# ============================================================

print("\nCreating MobileNetV3 Large...")

model = models.mobilenet_v3_large(
    weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
)


# ============================================================
# 12. FREEZE PRETRAINED FEATURES
# ============================================================

print("\nFreezing pretrained feature extractor...")

for param in model.features.parameters():
    param.requires_grad = False

print("Feature extractor frozen.")


# ============================================================
# 13. REPLACE CLASSIFIER
# ============================================================

model.classifier = nn.Sequential(
    nn.Linear(960, 1280),
    nn.Hardswish(),
    nn.Dropout(0.2),
    nn.Linear(
        1280,
        num_classes
    )
)

model = model.to(device)

print(
    f"\nClassifier created for "
    f"{num_classes} tomato classes."
)

print("Model created successfully.")


# ============================================================
# 14. LOSS FUNCTION
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# ============================================================
# 15. OPTIMIZER
# ============================================================

# Only train the new classifier.
optimizer = torch.optim.Adam(
    model.classifier.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# 16. LEARNING RATE SCHEDULER
# ============================================================

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    patience=2,
    factor=0.5
)


# ============================================================
# 17. TRAINING
# ============================================================

best_validation_accuracy = 0.0

print("\n")
print("=" * 60)
print("STARTING CPU-FRIENDLY TRANSFER LEARNING")
print("=" * 60)

print(
    f"Epochs: {EPOCHS}"
)

print(
    f"Batch size: {BATCH_SIZE}"
)

print(
    f"Learning rate: {LEARNING_RATE}"
)


for epoch in range(EPOCHS):

    print(
        f"\nEpoch {epoch + 1}/{EPOCHS}"
    )


    # ========================================================
    # TRAINING
    # ========================================================

    model.train()

    # Keep feature extractor in evaluation mode
    # so frozen BatchNorm layers don't update.
    model.features.eval()

    running_loss = 0.0

    correct = 0
    total = 0

    train_bar = tqdm(
        train_loader,
        desc="Training",
        ncols=100
    )


    for images, labels in train_bar:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        _, predictions = torch.max(
            outputs,
            1
        )

        total += labels.size(0)

        correct += (
            predictions == labels
        ).sum().item()

        train_bar.set_postfix(
            loss=f"{loss.item():.4f}"
        )


    train_loss = (
        running_loss /
        len(train_loader)
    )

    train_accuracy = (
        correct /
        total
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    model.eval()

    validation_loss = 0.0

    validation_correct = 0

    validation_total = 0

    validation_bar = tqdm(
        validation_loader,
        desc="Validation",
        ncols=100
    )


    with torch.no_grad():

        for images, labels in validation_bar:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            validation_loss += loss.item()

            _, predictions = torch.max(
                outputs,
                1
            )

            validation_total += (
                labels.size(0)
            )

            validation_correct += (
                predictions == labels
            ).sum().item()


    validation_loss /= (
        len(validation_loader)
    )

    validation_accuracy = (
        validation_correct /
        validation_total
    )


    # ========================================================
    # LEARNING RATE UPDATE
    # ========================================================

    scheduler.step(
        validation_loss
    )


    # ========================================================
    # RESULTS
    # ========================================================

    print(
        f"\nTrain Loss: "
        f"{train_loss:.4f}"
    )

    print(
        f"Train Accuracy: "
        f"{train_accuracy * 100:.2f}%"
    )

    print(
        f"Validation Loss: "
        f"{validation_loss:.4f}"
    )

    print(
        f"Validation Accuracy: "
        f"{validation_accuracy * 100:.2f}%"
    )

    print(
        f"Learning Rate: "
        f"{optimizer.param_groups[0]['lr']:.6f}"
    )


    # ========================================================
    # SAVE BEST MODEL
    # ========================================================

    if (
        validation_accuracy >
        best_validation_accuracy
    ):

        best_validation_accuracy = (
            validation_accuracy
        )

        torch.save(
            model.state_dict(),
            MODEL_OUTPUT
        )

        print(
            "\n*** NEW BEST MODEL SAVED ***"
        )

        print(
            f"Validation Accuracy: "
            f"{validation_accuracy * 100:.2f}%"
        )

        print(
            f"Saved to:"
        )

        print(
            MODEL_OUTPUT
        )


# ============================================================
# 18. TRAINING COMPLETE
# ============================================================

print("\n")
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print(
    f"Best Validation Accuracy: "
    f"{best_validation_accuracy * 100:.2f}%"
)

print("\nModel:")
print(MODEL_OUTPUT)

print("\nClasses:")
print(CLASS_OUTPUT)

print(
    "\nTomato model training finished successfully."
)