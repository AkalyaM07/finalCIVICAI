import joblib
import os
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "text_model.pkl"
)
model = joblib.load(MODEL_PATH)
DEPARTMENT_MAP = {
    "Pothole": "Roads Department",
    "Garbage": "Sanitation Department",
    "Drainage": "Drainage Department",
    "Flooding": "Disaster Management Department",
    "Water Leakage": "Water Department",
    "Streetlight": "Electrical Department",
    "Traffic Signal": "Traffic Department",
    "Road Obstruction": "Roads Department",
    "Infrastructure Damage": "Public Works Department"
}
PRIORITY_MAP = {
    "Pothole": ("HIGH", 48),
    "Garbage": ("MEDIUM", 48),
    "Drainage": ("HIGH", 24),
    "Flooding": ("CRITICAL", 12),
    "Water Leakage": ("HIGH", 24),
    "Streetlight": ("MEDIUM", 48),
    "Traffic Signal": ("CRITICAL", 12),
    "Road Obstruction": ("HIGH", 24),
    "Infrastructure Damage": ("HIGH", 48)
}
def analyze_complaint(text):
    if not text or not text.strip():
        return {
            "category": "Unknown",
            "confidence": 0,
            "priority": "MEDIUM",
            "department": "Municipal General Department",
            "sla_hours": 48
        }
    prediction = model.predict([text])[0]
    confidence = 0
    if hasattr(model, "decision_function"):
        scores = model.decision_function([text])
        if len(scores.shape) > 1:
            scores = scores[0]
        max_score = max(scores)
        confidence = round(
            (max_score / (abs(max_score) + 1)) * 100,
            2
        )
        confidence = max(0, confidence)
    elif hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([text])[0]
        confidence = round(
            max(probabilities) * 100,
            2
        )
    department = DEPARTMENT_MAP.get(
        prediction,
        "Municipal General Department"
    )
    priority, sla_hours = PRIORITY_MAP.get(
        prediction,
        ("MEDIUM", 48)
    )
    return {
        "category": prediction,
        "confidence": confidence,
        "priority": priority,
        "department": department,
        "sla_hours": sla_hours
    }