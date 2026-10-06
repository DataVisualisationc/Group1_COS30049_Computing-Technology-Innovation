WIND SPEED REGRESSION

Target:
  wind_speed_10m_max (km/h)

Features:
  surface_pressure_mean
  surface_pressure_max
  surface_pressure_min
  pressure_change
  wind_direction_10m_dominant

Models:
  Multiple Linear Regression
  Gradient Boosting Regressor
  HistGradientBoostingRegressor

Workflow:
1. python preprocess_wind.py
2. Open train_wind_models_split.ipynb in Jupyter/VS Code and Run All
3. python test_trained_model.py

Core packages:
  python -m pip install pandas numpy matplotlib scikit-learn joblib jupyter

Training / testing:
  2023-2025: training
  2026: testing
