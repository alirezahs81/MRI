import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# File names
RAW_DATA_FILE = os.path.join(RAW_DATA_DIR, "diabetes.csv")
PROCESSED_TRAIN_FILE = os.path.join(PROCESSED_DATA_DIR, "train_processed.csv")
PROCESSED_TEST_FILE = os.path.join(PROCESSED_DATA_DIR, "processed_test.csv")
MODEL_FILE = os.path.join(MODELS_DIR, "best_diabetes_model.joblib")
SCALER_FILE = os.path.join(MODELS_DIR, "scaler.joblib")

# Model training configurations
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
TARGET_COLUMN = "Outcome"
