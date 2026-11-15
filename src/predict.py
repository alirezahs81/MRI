import joblib
import numpy as np
import pandas as pd
import os
from src.config import MODEL_FILE, SCALER_FILE

class DiabetesPredictor:
    """
    Handles inference/prediction for new patient data using the trained model and scaler.
    """
    def __init__(self):
        if not os.path.exists(MODEL_FILE) or not os.path.exists(SCALER_FILE):
            raise FileNotFoundError("Trained model or scaler not found. Please train the model first using main.py.")
        
        self.model = joblib.load(MODEL_FILE)
        self.scaler = joblib.load(SCALER_FILE)

    def predict(self, input_data: list) -> dict:
        """
        Takes raw patient feature values, scales them, and returns prediction and probability.
        Expected input features order:
        [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age]
        """
        # Convert input to numpy array and reshape for single sample prediction
        input_array = np.array(input_data).reshape(1, -1)
        
        # Scale input features
        scaled_input = self.scaler.transform(input_array)
        
        # Make prediction
        prediction = self.model.predict(scaled_input)[0]
        
        # Get probability if available
        probability = None
        if hasattr(self.model, "predict_proba"):
            probability = float(self.model.predict_proba(scaled_input)[0][1])

        result = {
            "prediction": int(prediction),
            "result_text": "Positive (High Risk of Diabetes)" if prediction == 1 else "Negative (Low Risk of Diabetes)",
            "probability": probability
        }
        return result

if __name__ == "__main__":
    # Example sample for testing prediction
    # [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age]
    sample_patient = [6, 148, 72, 35, 0, 33.6, 0.627, 50]
    
    try:
        predictor = DiabetesPredictor()
        res = predictor.predict(sample_patient)
        print("Prediction Result:", res)
    except Exception as e:
        print("Error:", e)
