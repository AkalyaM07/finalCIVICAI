from image_engine import analyze_image

image_path = input(
    "Enter image path: "
)

result = analyze_image(
    image_path
)

print("\n========== IMAGE AI ANALYSIS ==========")

print(
    "Detected:",
    result["category"]
)

print(
    "Confidence:",
    result["confidence"],
    "%"
)

if "error" in result:
    print(
        "Error:",
        result["error"]
    )

print("======================================")