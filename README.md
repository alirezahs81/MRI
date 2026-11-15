# 🧠 Brain Tumor MRI Detection & 3D Reconstruction

An advanced end-to-end Python pipeline for medical image processing, brain tumor segmentation, and interactive 3D volumetric visualization from MRI scans.

---

## 🚀 Key Features

- **MRI Preprocessing:** Normalizes pixel intensity, applies robust noise reduction filters, and resizes volumetric scans.
- **Tumor Segmentation:** Extracts precise tumor regions and generates binary segmentation masks.
- **3D Surface Reconstruction:** Converts 2D segmentation slices into an interactive 3D volumetric model using Plotly.
- **Modular Architecture:** Clean, well-tested, object-oriented Python codebase designed for extensibility and readability.
- **Automated Testing:** Unit tests included to ensure robust pipeline execution.

---

## 🛠️ Project Structure

```text
Brain-Tumor-3D-Detection/
│
├── data/                  # MRI dataset storage or pointers
├── models/                # Trained deep learning model weights
├── src/
│   ├── __init__.py
│   ├── preprocessing.py   # MRI intensity normalization and noise filtering
│   ├── segmentation.py    # Tumor boundary extraction and segmentation
│   ├── reconstruction.py  # 3D surface mesh generation and Plotly rendering
│   └── main.py            # End-to-end pipeline runner
│
├── notebooks/             # Exploratory Jupyter Notebooks
├── tests/                 # Unit tests (pytest)
├── .gitignore             # Git ignore rules for cached & large files
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Brain-Tumor-3D-Detection.git
   cd Brain-Tumor-3D-Detection
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

Run the complete pipeline (simulation, preprocessing, segmentation, and 3D reconstruction):

```bash
$env:PYTHONPATH="."
python src/main.py
```

Run unit tests:
```bash
python -m pytest tests/test_pipeline.py
```

---

## 🧪 Testing

The project uses `pytest` for unit testing. To run tests:
```bash
python -m pytest
```

---

## 📜 License

This project is open-source under the [MIT License](LICENSE).
