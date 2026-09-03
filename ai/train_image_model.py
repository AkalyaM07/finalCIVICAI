import os
import torch
from torchvision import datasets, transforms, models
from torch import nn, optim
from torch.utils.data import DataLoader
DATA_DIR = "image_dataset/train"
BATCH_SIZE = 16
EPOCHS = 10
IMAGE_SIZE = 224
LEARNING_RATE = 0.001
MODEL_OUTPUT = "ai/image_model.pth"
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])
print("\nLoading image dataset...")
dataset = datasets.ImageFolder(
    DATA_DIR,
    transform=transform
)
print("\nClasses:")
for i, class_name in enumerate(dataset.classes):
    print(i, "->", class_name)
print("\nTotal images:", len(dataset))
loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
print("\nTraining device:", device)
print("\nLoading MobileNetV2...")
model = models.mobilenet_v2(
    weights="DEFAULT"
)
for parameter in model.features.parameters():
    parameter.requires_grad = False
num_classes = len(dataset.classes)
model.classifier[1] = nn.Linear(
    model.last_channel,
    num_classes
)
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(
    model.classifier[1].parameters(),
    lr=LEARNING_RATE
)
print("\n========== TRAINING STARTED ==========\n")
for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        _, predicted = torch.max(
            outputs,
            1
        )
        total += labels.size(0)
        correct += (
            predicted == labels
        ).sum().item()
    accuracy = (
        100 * correct / total
    )
    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Loss: {total_loss:.4f} "
        f"Accuracy: {accuracy:.2f}%"
    )
os.makedirs("ai", exist_ok=True)
torch.save(
    {
        "model_state": model.state_dict(),
        "classes": dataset.classes
    },
    MODEL_OUTPUT
)
print("\n========== TRAINING COMPLETE ==========")
print("Model saved to:")
print(MODEL_OUTPUT)
print("\nClasses saved:")
print(dataset.classes)