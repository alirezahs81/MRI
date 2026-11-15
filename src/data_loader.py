import os
import pandas as pd
from sklearn.datasets import load_diabetes
from src.config import RAW_DATA_FILE, RAW_DATA_DIR

class DataLoader:
    """
    Handles data loading. If the local dataset doesn't exist,
    it downloads or generates the standard diabetes classification dataset (Pima Indians equivalent).
    """
    def __init__(self, data_path: str = RAW_DATA_FILE):
        self.data_path = data_path

    def load_data(self) -> pd.DataFrame:
        """Loads data from CSV or fetches the standard classification dataset if not present."""
        if os.path.exists(self.data_path):
            print(f"Loading data from local file: {self.data_path}")
            return pd.read_csv(self.data_path)
        else:
            print("Local dataset not found. Downloading standard Diabetes classification dataset...")
            return self._fetch_and_save_dataset()

    def _fetch_and_save_dataset(self) -> pd.DataFrame:
        """Fetches the Pima Indians Diabetes dataset from a reliable public source or sklearn/uci."""
        # Using a reliable public CSV URL for the Pima Indians Diabetes Database
        url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
        column_names = [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"
        ]
        
        try:
            df = pd.read_csv(url, names=column_names)
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            df.to_csv(self.data_path, index=False)
            print(f"Dataset successfully downloaded and saved to {self.data_path}")
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to download dataset: {e}")

if __name__ == "__main__":
    loader = DataLoader()
    df = loader.load_data()
    print("Dataset shape:", df.shape)
    print(df.head())
