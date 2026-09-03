import os
import torch
from torchvision import transforms, models
from PIL import Image
from torch import nn


# =========================================================
# MODEL PATH
# =========================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "image_model.pth"
)


# =========================================================
# DEVICE
# =========================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# =========================================================
# LOAD CHECKPOINT
# =========================================================

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device
)


# =========================================================
# LOAD CLASS NAMES
# =========================================================

classes = checkpoint["classes"]


# =========================================================
# CREATE MOBILENETV2
# =========================================================

model = models.mobilenet_v2(
    weights=None
)

model.classifier[1] = nn.Linear(
    model.last_channel,
    len(classes)
)


# =========================================================
# LOAD TRAINED WEIGHTS
# =========================================================

model.load_state_dict(
    checkpoint["model_state"]
)

model = model.to(device)
model.eval()


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# =========================================================
# ANALYZE IMAGE
# =========================================================

def analyze_image(image_path):

    try:

        # Open image
        image = Image.open(
            image_path
        ).convert("RGB")

        # Preprocess image
        image = transform(image)

        # Add batch dimension
        image = image.unsqueeze(0)

        # Move to CPU/GPU
        image = image.to(device)

        # Prediction
        with torch.no_grad():

            output = model(image)

            probabilities = torch.softmax(
                output,
                dim=1
            )

            confidence, prediction = torch.max(
                probabilities,
                dim=1
            )

        # Get predicted category
        category = classes[
            prediction.item()
        ]

        # Convert confidence to percentage
        confidence = round(
            confidence.item() * 100,
            2
        )

        return {
            "category": category,
            "confidence": confidence
        }

    except Exception as e:

        return {
            "category": "Unknown",
            "confidence": 0,
            "error": str(e)
        }