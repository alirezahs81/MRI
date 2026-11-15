from src.data_loader import DataLoader
from src.preprocessing import DataPreprocessor
from src.train import ModelTrainer
from src.evaluate import ModelEvaluator
from src.predict import DiabetesPredictor
import joblib
import os
from src.config import MODEL_FILE

def main():
    print("=== Starting Diabetes Prediction Pipeline ===")

    # Step 1: Load Data
    print("\n[Step 1/4] Loading Data...")
    loader = DataLoader()
    df = loader.load_data()
    print(f"Data loaded successfully with shape: {df.shape}")

    # Step 2: Preprocess Data
    print("\n[Step 2/4] Preprocessing Data & Scaling...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, feature_names = preprocessor.preprocess_pipeline(df)
    print("Preprocessing completed. Training set shape:", X_train.shape)

    # Step 3: Train Model
    print("\n[Step 3/4] Training Models & Selecting Best Estimator...")
    trainer = ModelTrainer()
    best_model = trainer.train_and_evaluate(X_train, y_train, X_test, y_test)

    # Step 4: Evaluate Model
    print("\n[Step 4/4] Evaluating Best Model...")
    y_pred = best_model.predict(X_test)
    y_prob = best_model.predict_proba(X_test)[:, 1] if hasattr(best_model, "predict_proba") else None
    ModelEvaluator.print_evaluation_report(y_test, y_pred, y_prob)

    # Quick Demo of Prediction Module
    print("\n--- Running Sample Inference ---")
    predictor = DiabetesPredictor()
    sample_patient = [2, 120, 70, 20, 79, 25.5, 0.254, 30]
    prediction_result = predictor.predict(sample_patient)
    print("Sample Patient Features:", sample_patient)
    print("Prediction Result:", prediction_result)

    print("\n=== Pipeline Completed Successfully! ===")

if __name__ == "__main__":
    main()
