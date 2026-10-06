<<<<<<< HEAD
<<<<<<< HEAD
# JMA Typhoon Landfall Risk Prediction Pipeline

This README documents the complete data-processing, model-training, and
testing pipeline.

## Complete Pipeline

``` text
bst_all.txt
   │
   ▼
build_jma_day3_landfall_dataset.py
   │
   │  • Parse JMA Best Track data
   │  • Find confirmed "#" landfall events
   │  • Create Day -3, -2, -1, Day 0 rows
   │  • Assign:
   │      Day -3 = Low
   │      Day -2 = Moderate
   │      Day -1 = High
   │      Day  0 = High
   │
   ▼
jma_day3_to_landfall_before_weather.csv
   │
   ▼
download_openmeteo_daily_landfall.py
   │
   │  • Use each row/date to retrieve DAILY weather
   │  • Temperature
   │  • Humidity
   │  • Dew point
   │  • Rain / precipitation
   │  • Cloud cover
   │  • Pressure
   │  • Wind speed / gust
   │  • Wind direction
   │  • Shortwave radiation
   │
   ▼
jma_day3_to_landfall_with_weather.csv
   │
   ▼
add_nearest_prefecture.py
   │
   │  + jp_shp/
   │
   │  • Determine nearest Japanese prefecture
   │  • Add:
   │      nearest_prefecture
   │      distance_to_prefecture_km
   │
   ▼
jma_day3_to_landfall_with_weather_prefecture.csv
   │
   ▼
train_landfall_models_event_split.py
   │
   │  INPUT:
   │  jma_day3_to_landfall_with_weather_prefecture.csv
   │
   │  • Remove leakage / unwanted features
   │
   │  EXCLUDED:
   │      risk (becomes target)
   │      days_before_landfall
   │      relative_day
   │      is_landfall_day
   │      landfall
   │      event/storm IDs
   │      raw datetime columns
   │      hour
   │      latitude
   │      longitude
   │      openmeteo_latitude
   │      openmeteo_longitude
   │      distance_to_prefecture_km
   │      download/processing columns
   │
   │  KEPT:
   │      nearest_prefecture
   │      JMA typhoon attributes
   │      daily weather attributes
   │      year / month / day
   │
   │  • Split by landfall_event_id
   │      80% training events
   │      20% testing events
   │
   │  • Preprocessing
   │      Numeric → median → StandardScaler
   │      Categorical → impute → OneHotEncoder
   │
   │  • Train:
   │      Random Forest
   │      CART
   │      Gradient Boosting
   │      SVM
   │
   ▼
trained_models/
   │
   ├── training_set.csv
   ├── testing_set.csv
   ├── model_comparison_results.csv
   │
   ├── random_forest_model.joblib
   ├── cart_model.joblib
   ├── gradient_boosting_model.joblib
   └── svm_model.joblib
   │
   ▼
test_trained_model.py
   │
   │  • Load trained .joblib model
   │  • Load testing_set.csv
   │  • Select unseen test row
   │  • Apply same preprocessing
   │  • model.predict(...)
   │
   ▼
FINAL RESULT

Actual Risk:     Low / Moderate / High
Predicted Risk:  Low / Moderate / High

+ prediction probabilities (where supported)
```

## Risk Labels

  Relative Day   Risk
  -------------- ----------
  Day -3         Low
  Day -2         Moderate
  Day -1         High
  Day 0          High

## Models

-   Random Forest
-   CART (Decision Tree)
-   Gradient Boosting
-   Support Vector Machine (SVM)

## Train/Test Strategy

The dataset is split by `landfall_event_id`, not by individual rows.

-   80% of landfall events are used for training.
-   20% of landfall events are used for testing.
-   Rows from the same landfall event remain together to prevent event
    leakage.

## Final Prediction

The target variable is `risk`. The classifier outputs `Low`, `Moderate`,
or `High`.

`test_trained_model.py` loads a trained model and the held-out testing
set, makes a prediction, compares it with the actual risk, and displays
prediction probabilities where supported.
=======
=======
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
# JMA Typhoon Landfall Risk Prediction

## Folder Structure

```text
Typhoon/
├── README.md
├── data/
│   ├── raw/
│   │   └── bst_all.txt
│   ├── processed/
│   │   ├── jma_day3_to_landfall_before_weather.csv
│   │   ├── jma_day3_to_landfall_with_weather.csv
│   │   └── jma_day3_to_landfall_with_weather_prefecture.csv
│   └── gis/
│       └── jp_shp/
├── preprocessing/
│   ├── build_jma_day3_landfall_dataset.py
│   ├── download_openmeteo_daily_landfall.py
│   └── add_nearest_prefecture.py
├── training/
│   ├── train_landfall_models_event_split.py
│   └── trained_models/
└── testing/
    └── test_trained_model.py
```

## Pipeline

1. `preprocessing/build_jma_day3_landfall_dataset.py`
   - Reads `data/raw/bst_all.txt`.
   - Creates Day -3, Day -2, Day -1 and Day 0 records.
   - Risk: Day -3 = Low, Day -2 = Moderate, Day -1/0 = High.

2. `preprocessing/download_openmeteo_daily_landfall.py`
   - Adds daily Open-Meteo weather attributes.
   - Writes progress and final weather data under `data/processed/`.

3. `preprocessing/add_nearest_prefecture.py`
   - Uses `data/gis/jp_shp/`.
   - Adds nearest Japanese prefecture and distance.

4. `training/train_landfall_models_event_split.py`
   - Reads the final processed dataset.
   - Splits by `landfall_event_id` (80% training events / 20% testing events).
   - Trains Random Forest, CART, Gradient Boosting and SVM.
   - Saves all artifacts under `training/trained_models/`.

5. `testing/test_trained_model.py`
   - Loads `training/trained_models/gradient_boosting_model.joblib`.
   - Tests against `training/trained_models/testing_set.csv`.

## Run

From the `Typhoon` folder:

```powershell
python preprocessing/build_jma_day3_landfall_dataset.py
python preprocessing/download_openmeteo_daily_landfall.py
python preprocessing/add_nearest_prefecture.py
python training/train_landfall_models_event_split.py
python testing/test_trained_model.py
```

## GIS data

Copy your existing `jp_shp` folder into:

```text
data/gis/jp_shp/
```

## Existing trained models

Copy your existing `.joblib` files and generated training/testing CSVs into:

```text
training/trained_models/
```
<<<<<<< HEAD
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
=======
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
