import joblib
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from src.config import MODEL_FILE, RANDOM_STATE, CV_FOLDS

class ModelTrainer:
    """
    Trains multiple machine learning models and selects the best performing one.
    """
    def __init__(self):
        self.models = {
            "LogisticRegression": LogisticRegression(random_state=RANDOM_STATE, max_iter=1000),
            "RandomForest": RandomForestClassifier(random_state=RANDOM_STATE),
            "XGBoost": XGBClassifier(random_state=RANDOM_STATE, eval_metric='logloss')
        }
        self.best_model = None
        self.best_model_name = None

    def train_and_evaluate(self, X_train, y_train, X_test, y_test):
        """Trains models, evaluates them on test set, and saves the best model."""
        best_score = 0.0

        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            print(f"{name} Test Accuracy: {score:.4f}")

            if score > best_score:
                best_score = score
                self.best_model = model
                self.best_model_name = name

        print(f"\nBest Model Selected: {self.best_model_name} with Accuracy: {best_score:.4f}")

        # Save the best model
        os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
        joblib.dump(self.best_model, MODEL_FILE)
        print(f"Best model successfully saved to {MODEL_FILE}")

        return self.best_model

if __name__ == "__main__":
    from src.data_loader import DataLoader
    from src.preprocessing import DataPreprocessor

    loader = DataLoader()
    df = loader.load_data()

    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, _ = preprocessor.preprocess_pipeline(df)

    trainer = ModelTrainer()
    best_model = trainer.train_and_evaluate(X_train, y_train, X_test, y_test)
