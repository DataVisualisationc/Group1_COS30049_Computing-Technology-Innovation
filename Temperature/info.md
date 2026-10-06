# Temperature Regression

Inputs: shortwave radiation, sunshine duration, daylight duration, cloud cover, mean dew point, month.
Output: daily maximum temperature (`temperature_2m_max`) (°C).

Models:
1. Multiple Linear Regression
2. Gradient Boosting Regressor
3. HistGradientBoostingRegressor

Split: 2023–2025 training, 2026 testing.

Run:
1. `python preprocess_temperature.py`
2. Run `train_temperature_max_models_split.ipynb`
3. `python test_trained_model.py`
