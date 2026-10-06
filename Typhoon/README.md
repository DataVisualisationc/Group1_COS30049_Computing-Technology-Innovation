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
