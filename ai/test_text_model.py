import joblib
model = joblib.load("ai/text_model.pkl")
test_complaints = [
    "There is a huge pothole near my college",
    "Garbage is overflowing near the bus stop",
    "The drainage is completely blocked",
    "Water is leaking from the street pipe",
    "The streetlight is not working"
]
for complaint in test_complaints:
    prediction = model.predict([complaint])[0]
    print("\nComplaint:")
    print(complaint)
    print("Predicted Category:")
    print(prediction)