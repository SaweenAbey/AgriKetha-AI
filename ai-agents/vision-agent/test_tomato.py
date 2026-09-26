import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report,
    confusion_matrix
)


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "Tomato Leaf Disease"
)

TEST_DIR = os.path.join(
    DATA_DIR,
    "test"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "best_tomato_model.pth"
)

CLASS_PATH = os.path.join(
    BASE_DIR,
    "tomato_classes.txt"
)

IMAGE_SIZE = 224
BATCH_SIZE = 8


# ============================================================
# 2. DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("=" * 60)
print("TOMATO MODEL TEST EVALUATION")
print("=" * 60)

print(f"Device: {device}")


# ============================================================
# 3. CHECK REQUIRED FILES
# ============================================================

if not os.path.exists(TEST_DIR):
    raise FileNotFoundError(
        f"Test directory not found:\n{TEST_DIR}"
    )

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Tomato model not found:\n{MODEL_PATH}"
    )

if not os.path.exists(CLASS_PATH):
    raise FileNotFoundError(
        f"Class file not found:\n{CLASS_PATH}"
    )


# ============================================================
# 4. TEST TRANSFORM
# ============================================================

test_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMAGE_SIZE),

    transforms.ToTensor(),

    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])


# ============================================================
# 5. LOAD CLASS NAMES
# ============================================================

with open(
    CLASS_PATH,
    "r",
    encoding="utf-8"
) as f:

    class_names = [
        line.strip()
        for line in f
        if line.strip()
    ]


num_classes = len(class_names)

print(
    f"\nNumber of classes: "
    f"{num_classes}"
)

print("\nClass mapping:")

for i, name in enumerate(class_names):
    print(
        f"  {i}: {name}"
    )


# ============================================================
# 6. LOAD TEST DATASET
# ============================================================

print("\nLoading test dataset...")

test_dataset = datasets.ImageFolder(
    root=TEST_DIR,
    transform=test_transform
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

print(
    f"\nTotal test images: "
    f"{len(test_dataset)}"
)


# ============================================================
# 7. VERIFY CLASS ORDER
# ============================================================

print("\nChecking class order...")

if test_dataset.classes != class_names:

    print(
        "\nWARNING: Class order mismatch!"
    )

    print(
        "\nClasses from test dataset:"
    )

    print(
        test_dataset.classes
    )

    print(
        "\nClasses from "
        "tomato_classes.txt:"
    )

    print(
        class_names
    )

    raise ValueError(
        "\nClass order mismatch. "
        "Evaluation stopped to prevent "
        "incorrect results."
    )

print(
    "Class order verified successfully."
)


# ============================================================
# 8. CREATE MOBILENETV3 LARGE
# ============================================================

print(
    "\nLoading MobileNetV3 Large..."
)

model = models.mobilenet_v3_large(
    weights=None
)


# ============================================================
# 9. CREATE SAME CLASSIFIER
#    USED DURING TRAINING
# ============================================================

model.classifier = nn.Sequential(
    nn.Linear(
        960,
        1280
    ),

    nn.Hardswish(),

    nn.Dropout(
        0.2
    ),

    nn.Linear(
        1280,
        num_classes
    )
)


# ============================================================
# 10. LOAD TRAINED WEIGHTS
# ============================================================

print(
    "\nLoading trained tomato model..."
)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=device
    )
)

model = model.to(device)

model.eval()

print(
    "Model loaded successfully."
)


# ============================================================
# 11. TEST MODEL
# ============================================================

criterion = nn.CrossEntropyLoss()

total_loss = 0.0

correct = 0
total = 0

all_predictions = []
all_labels = []

print(
    "\nStarting test evaluation..."
)

print(
    "Please wait while all test images "
    "are evaluated.\n"
)


with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)

        labels = labels.to(device)

        # Forward pass
        outputs = model(images)

        # Calculate loss
        loss = criterion(
            outputs,
            labels
        )

        total_loss += (
            loss.item()
            * labels.size(0)
        )

        # Get prediction
        _, predictions = torch.max(
            outputs,
            1
        )

        # Total images
        total += labels.size(0)

        # Correct predictions
        correct += (
            predictions == labels
        ).sum().item()

        # Store predictions
        all_predictions.extend(
            predictions.cpu().numpy()
        )

        # Store actual labels
        all_labels.extend(
            labels.cpu().numpy()
        )


# ============================================================
# 12. OVERALL TEST RESULTS
# ============================================================

test_loss = (
    total_loss / total
)

test_accuracy = (
    correct / total
)

print("\n")
print("=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)

print(
    f"Test Loss: "
    f"{test_loss:.4f}"
)

print(
    f"Test Accuracy: "
    f"{test_accuracy * 100:.2f}%"
)

print(
    f"Correct Predictions: "
    f"{correct}/{total}"
)


# ============================================================
# 13. PER-CLASS PERFORMANCE
# ============================================================

print("\n")
print("=" * 60)
print("PER-CLASS PERFORMANCE")
print("=" * 60)

report = classification_report(
    all_labels,
    all_predictions,
    target_names=class_names,
    digits=4,
    zero_division=0
)

print(report)


# ============================================================
# 14. CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_labels,
    all_predictions
)

print("=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(
    "\nRows = Actual"
)

print(
    "Columns = Predicted\n"
)

print(cm)


# ============================================================
# 15. PER-CLASS ACCURACY
# ============================================================

print("\n")
print("=" * 60)
print("PER-CLASS ACCURACY")
print("=" * 60)

for i, class_name in enumerate(
    class_names
):

    class_total = cm[i].sum()

    class_correct = cm[
        i,
        i
    ]

    if class_total > 0:

        class_accuracy = (
            class_correct /
            class_total
        ) * 100

    else:

        class_accuracy = 0.0

    print(
        f"{class_name}: "
        f"{class_accuracy:.2f}% "
        f"({class_correct}/{class_total})"
    )


# ============================================================
# 16. PEST PERFORMANCE
# ============================================================

print("\n")
print("=" * 60)
print("PEST PERFORMANCE")
print("=" * 60)

pest_class = (
    "Tomato___Spider_mites "
    "Two-spotted_spider_mite"
)

if pest_class in class_names:

    pest_index = class_names.index(
        pest_class
    )

    pest_total = cm[
        pest_index
    ].sum()

    pest_correct = cm[
        pest_index,
        pest_index
    ]

    if pest_total > 0:

        pest_accuracy = (
            pest_correct /
            pest_total
        ) * 100

    else:

        pest_accuracy = 0.0

    print(
        f"Spider Mites Accuracy: "
        f"{pest_accuracy:.2f}%"
    )

    print(
        f"Correct: "
        f"{pest_correct}/{pest_total}"
    )

else:

    print(
        "Spider Mites class not found."
    )


# ============================================================
# 17. HEALTHY CLASS PERFORMANCE
# ============================================================

print("\n")
print("=" * 60)
print("HEALTHY CLASS PERFORMANCE")
print("=" * 60)

healthy_class = (
    "Tomato___healthy"
)

if healthy_class in class_names:

    healthy_index = class_names.index(
        healthy_class
    )

    healthy_total = cm[
        healthy_index
    ].sum()

    healthy_correct = cm[
        healthy_index,
        healthy_index
    ]

    if healthy_total > 0:

        healthy_accuracy = (
            healthy_correct /
            healthy_total
        ) * 100

    else:

        healthy_accuracy = 0.0

    print(
        f"Healthy Accuracy: "
        f"{healthy_accuracy:.2f}%"
    )

    print(
        f"Correct: "
        f"{healthy_correct}/{healthy_total}"
    )

else:

    print(
        "Healthy class not found."
    )


# ============================================================
# 18. FINISHED
# ============================================================

print("\n")
print("=" * 60)
print("TEST EVALUATION COMPLETE")
print("=" * 60)