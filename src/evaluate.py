import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, classification_report, confusion_matrix
)

class ModelEvaluator:
    """
    Evaluates trained machine learning models using various medical and classification metrics.
    """
    @staticmethod
    def evaluate_predictions(y_true, y_pred, y_prob=None) -> dict:
        """
        Computes accuracy, precision, recall, f1-score, and roc-auc.
        """
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1_score": f1_score(y_true, y_pred, zero_division=0)
        }

        if y_prob is not None:
            try:
                metrics["roc_auc"] = roc_auc_score(y_true, y_prob)
            except Exception:
                metrics["roc_auc"] = None

        return metrics

    @staticmethod
    def print_evaluation_report(y_true, y_pred, y_prob=None):
        """Prints a detailed classification report and confusion matrix."""
        print("\n--- Model Evaluation Report ---")
        metrics = ModelEvaluator.evaluate_predictions(y_true, y_pred, y_prob)
        
        for metric_name, value in metrics.items():
            if value is not None:
                print(f"{metric_name.replace('_', ' ').capitalize()}: {value:.4f}")
            else:
                print(f"{metric_name.replace('_', ' ').capitalize()}: N/A")

        print("\nConfusion Matrix:")
        print(confusion_matrix(y_true, y_pred))
        
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred))

if __name__ == "__main__":
    from src.data_loader import DataLoader
    from src.preprocessing import DataPreprocessor
    import joblib
    from src.config import MODEL_FILE

    loader = DataLoader()
    df = loader.load_data()

    preprocessor = DataPreprocessor()
    _, X_test, _, y_test, _ = preprocessor.preprocess_pipeline(df)

    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
        ModelEvaluator.print_evaluation_report(y_test, y_pred, y_prob)
    else:
        print("Model file not found. Train the model first.")
