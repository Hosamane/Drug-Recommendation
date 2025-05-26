import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

# Load data
df = pd.read_csv("Training.csv")
X = df.drop("prognosis", axis=1)
y = df["prognosis"]

# Encode target labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y_encoded)

# Save both model and label encoder in one file
with open("disease_model_with_le.pkl", "wb") as f:
    pickle.dump({"model": model, "label_encoder": le}, f)

print("Model and Label Encoder saved together as disease_model_with_le.pkl")
