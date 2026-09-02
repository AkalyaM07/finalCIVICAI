from transformers import pipeline
from PIL import Image
image_classifier = pipeline(
    "image-classification",
    model="google/vit-base-patch16-224"
)
def analyze_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        results = image_classifier(image)
        prediction = results[0]
        label = prediction["label"]
        confidence = round(prediction["score"] * 100, 2)
        return {
            "label": label,
            "confidence": confidence
        }
    except Exception as e:
        return {
            "label": "Unknown",
            "confidence": 0,
            "error": str(e)
        }