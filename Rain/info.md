# Rainfall Classification

## Objective
Predict a daily rainfall category from daily weather attributes using classification.

## Target
`rain_class`, created from `rain_sum`:
- `< 1 mm`: No/Minimal Rain
- `1 to < 10 mm`: Low
- `10 to < 100 mm`: Moderate
- `>= 100 mm`: High

These are project-defined daily rainfall classes, not official JMA Low/Moderate/High categories.

## Input Features
- `temperature_2m_max`
- `temperature_2m_min`
- `relative_humidity_2m_mean`
- `dew_point_2m_mean`
- `cloud_cover_mean`
- `pressure_msl_mean`
- `wind_speed_10m_max`
- `shortwave_radiation_sum`
- `month`

`rain_sum` is not an input feature because it is used to construct the target. Using it as X would cause target leakage.

## Models
1. Gradient Boosting
2. Random Forest
3. CART (Decision Tree)
4. Support Vector Machine (SVM)

## Train/Test Split
- 2021-2025: training
- 2026: testing

A chronological split is used to keep future observations out of the training set.

## Evaluation
Models are evaluated using:
- Accuracy
- Macro Precision
- Macro Recall
- Macro F1
- Classification Report
- Confusion Matrix

Macro metrics are important because rainfall classes can be imbalanced.

## Project Structure
```text
Rain/
├── preprocess_rain.py
├── train_rain_models_split.ipynb
├── test_trained_model.py
├── README.md
├── dataset/
│   └── rain_preprocessed.csv
└── trained_models/
    ├── training.csv
    ├── testing.csv
    ├── gradient_boosting.joblib
    ├── random_forest.joblib
    ├── cart.joblib
    ├── svm.joblib
    └── model_results.csv
```

## Workflow

### 1. Preprocess
```powershell
python preprocess_rain.py
```

This creates `dataset/rain_preprocessed.csv`.

### 2. Train
Open `train_rain_models_split.ipynb` in Jupyter or VS Code and run all cells.

To launch Jupyter:
```powershell
python -m notebook
```

The notebook visualises the dataset, performs the chronological split, trains the four classifiers, evaluates them, and saves the trained models.

### 3. Test
```powershell
python test_trained_model.py
```

The testing script lets you choose a trained model and either enter weather attributes manually or test an observation from `testing.csv`.

## Required Packages
```powershell
python -m pip install pandas numpy matplotlib scikit-learn joblib jupyter
```

## Important Notes
- `rain_sum` may remain in processed/testing CSV files for evaluation, but it must never be passed to `model.predict()`.
- The models predict rainfall categories, not exact rainfall in millimetres.
- Daily weather data is used rather than hourly weather data.
- Keep the 2021-2025 training / 2026 testing split when comparing models.
