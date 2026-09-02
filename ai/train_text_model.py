import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
data = pd.read_csv("ai/complaints.csv")
X = data["text"]
y = data["category"]
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2)
    )),
    ("svm", LinearSVC())
])
model.fit(X_train, y_train)
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print("Text Classification Model")
print("-------------------------")
print(f"Accuracy: {accuracy:.2f}")
print()
print(classification_report(y_test, predictions))
joblib.dump(model, "ai/text_model.pkl")
print("Model saved successfully:")
print("ai/text_model.pkl")