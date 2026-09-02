from image_engine import analyze_image
image_path = input("Enter image path: ")
result = analyze_image(image_path)
print("\n========== IMAGE AI ANALYSIS ==========")
print("Image:", image_path)
print("Detected:", result["label"])
print("Confidence:", result["confidence"], "%")
print("=======================================")