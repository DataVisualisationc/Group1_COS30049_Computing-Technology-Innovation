# Model Input / Output Reference

Reference for preprocessing: each model's input (X) and output (y)

<<<<<<< HEAD
**(raw)** = pulled directly from Open-Meteo / source dataset  

**(created)** = engineered by us in preprocessing.

*You will find most of our models are **supervised** cuz we know what we want to predict output (Y)*

---

## Flood
**Machine Learning Model (Classification)**
- CART / Decision Tree - Always Strong first choice.
- Gradient Boosting Classifier - Good for learning more subtle relationships between discharge, rainfall history, elevation, and your engineered features.  
- ID3 (Iterative Dichotomiser 3) - information gain , but CART is always prefered than this.

**Input (X)**

1. `river_discharge`, `river_discharge_mean`, `river_discharge_median`, `river_discharge_max` - (raw)
2. `rain_sum_past_3day` - rolling 3-day sum of `rain_sum` - (created)
3. `rain_flag_50mm` - flag for any day where `rain_sum` > 50mm - (created)
4. `discharge_ratio` — flag for when `river_discharge` has tripled (3x) relative to its value 4 days prior — (created)
5. `elevation` — (raw, from location table)

**Output (y)**
Flood occurrence severity  (3-level flag):

1. Low
2. Medium
3. High

---

## Rain
**Machine Learning Model (Regression)**
- Gradient Boosting Regressor - can capture complex interactions between humidity/cloud/weather features.
- Linear Regression -  can test
- Random Forest - Always good

**Input (X)**

1. `relative_humidity_2m` — hourly, aggregate to daily (mean) — (raw)
2. `cloud_cover` — hourly, aggregate to daily (mean) — (raw)
3. `weather_code` — hourly, needs a daily conversion method — (raw, aggregation )

**Output (y)**

1. `rain_sum`
2. `precipitation_sum`
3. `precipitation_hours`

**Status / notes**

- `weather_code` is categorical (WMO codes) — averaging doesn't work. Use daily mode, or a derived proportion (e.g., % of hours reporting rain-type codes) instead.
- `rain_sum` and `precipitation_sum` will be highly correlated (precipitation = rain + snow) — check for redundancy before treating as 3 independent targets.

---

## Wind
**Machine Learning Model (Regression)**
- MARS - can handle nonlinear relationships by creating piecewise regression functions.
- Multiple Linear Regression - can show whether pressure changes have a relatively simple relationship with wind speed.


**Input (X)**

1. `surface_pressure_mean`, `surface_pressure_max` — daily aggregations, pull directly (no hourly aggregation needed) — (raw)
2. `surface_pressure_min` — if available, more diagnostic than mean/max for detecting approaching low-pressure systems — (raw)
3. `pressure_change` — day-over-day delta (today's pressure minus yesterday's) — (created)
4. `wind_direction_10m_dominant` — (raw)

**Output (y)**

1. `wind_speed_10m_max`
2. `wind_gusts_10m_max`

---

## Temp
**Machine Learning Model (Regression)**
- OLSR -assumes approximately linear relationships between radiation, sunshine, cloud cover, humidity and temperature without much preprocessing.

- Gradient Boosting Regressor - Strong candidate for accurate temperature prediction from structured weather variables.

**Input (X)**


1. `shortwave_radiation_sum` — (raw)
2. `sunshine_duration` — (raw)
3. `daylight_duration` — (raw)
4. `cloud_cover` — hourly, aggregate to daily — (raw)
5. `dew_point_2m` or `relative_humidity_2m` — (raw)


**Output (y)**

1. `temperature_2m_max`
2. `temperature_2m_min`



---

## Snow
**Machine Learning Model (Regression)**
- MARS - the relationship can change around certain temperatures. MARS is made for relationships like this because it divides the relationship into different regions.
- Random Forest Regressor - very safe
- Gradient Boosting Regression

**Input (X)**

1. `temperature_2m_min` — (raw)
2. `precipitation_sum` or `rain_sum` — (raw) [would be nice]

**Output (y)**

1. `snowfall_sum`

---
=======
**(raw)** = pulled directly from Open-Meteo / source dataset

**(created)** = engineered by us in preprocessing.

*You will find most of our models are **supervised** cuz we know what we
want to predict output (Y)*

------------------------------------------------------------------------

## Flood

**Machine Learning Model (Classification)** - CART / Decision Tree -
interpretable tree-based baseline. - Gradient Boosting Classifier -
captures nonlinear relationships between rainfall history, river
discharge, and engineered flood indicators. - ID3 (Iterative
Dichotomiser 3) - information-gain-based decision tree used for
comparison.

**Input (X)**

1.  `river_discharge` --- current river discharge --- (raw)
2.  `river_discharge_mean_7day` --- mean river discharge over the
    previous 7 days --- (created)
3.  `river_discharge_median_7day` --- median river discharge over the
    previous 7 days --- (created)
4.  `river_discharge_max_7day` --- maximum river discharge over the
    previous 7 days --- (created)
5.  `rain_sum_past_3day` --- total rainfall over the previous 3 days ---
    (created)
6.  `rain_sum_past_7day` --- total rainfall over the previous 7 days ---
    (created)
7.  `max_daily_rain_past_7day` --- maximum daily rainfall during the
    previous 7 days --- (created)
8.  `rain_flag_50mm` --- indicates whether rainfall reached the
    project's 50 mm condition --- (created)
9.  `precipitation_hours_past_7day` --- total precipitation hours over
    the previous 7 days --- (created)
10. `discharge_ratio` --- river-discharge increase relative to the
    earlier/baseline condition --- (created)
11. `elevation` --- (raw, from location table)

**Output (y)**

`flood_risk` --- flood occurrence severity:

1.  Low
2.  Medium
3.  High

**Reference dataset / threshold development**

-   `japan_flood_training_dataset.csv` contains 25 known flood examples
    and 25 non-flood examples.
-   This 50-row dataset is a **reference dataset**, not the final ML
    training dataset.
-   It is used to compare historical flood and non-flood conditions and
    derive candidate project thresholds.
-   Historical rolling conditions use the previous 7 complete days; the
    event day itself is excluded.

Current candidate project thresholds:

-   `rain_sum_past_3day >= 46.30`
-   `rain_sum_past_7day >= 71.40`
-   `max_daily_rain_past_7day >= 36.80`
-   `precipitation_hours_past_7day >= 58`
-   `river_discharge >= 9.47`
-   `river_discharge_mean_7day >= 2.64`
-   `river_discharge_max_7day >= 9.47`
-   `discharge_ratio >= 3.14`

These are project-derived candidate thresholds and are **not official
Japanese flood-warning thresholds**.

**Final dataset flow**

`Historical flood/non-flood reference -> derive conditions -> process individual daily Open-Meteo datasets -> calculate rolling indicators -> generate Low/Medium/High labels -> concatenate -> final ML dataset`

**Training / testing**

-   Training: 2023--2025
-   Testing: 2026-01-01 to 2026-01-31
-   Dates after 2026-01-31 are not required.

**Status / notes**

-   The final ML dataset comes from the larger individual daily
    Open-Meteo datasets, not directly from the 50-row historical
    reference dataset.
-   Rolling historical features should use shifted values so only
    information before the classified day is used.
-   The Low / Medium / High labelling method is project-defined and
    should be validated against the historical reference examples.
-   Because labels are generated from rainfall and river conditions,
    care is required to avoid target leakage when choosing model input
    features.

------------------------------------------------------------------------

## Rain

**Machine Learning Model (Classification)** - Gradient Boosting
Classifier - can capture nonlinear interactions between the daily
weather attributes. - Random Forest Classifier - robust ensemble model
and a strong general baseline. - CART / Decision Tree - simple and
interpretable classification baseline. - Support Vector Machine (SVM) -
useful for comparing a different classification approach.

**Input (X)**

1.  `temperature_2m_max` --- (raw)
2.  `temperature_2m_min` --- (raw)
3.  `relative_humidity_2m_mean` --- daily mean --- (raw)
4.  `dew_point_2m_mean` --- daily mean --- (raw)
5.  `cloud_cover_mean` --- daily mean --- (raw)
6.  `pressure_msl_mean` --- daily mean --- (raw)
7.  `wind_speed_10m_max` --- (raw)
8.  `shortwave_radiation_sum` --- (raw)
9.  `month` --- extracted from date --- (created)

**Output (y)**

`rain_class` --- created from daily `rain_sum`:

1.  No/Minimal Rain --- `< 1 mm`
2.  Low --- `1 to < 10 mm`
3.  Moderate --- `10 to < 100 mm`
4.  High --- `>= 100 mm`

**Status / notes**

-   `rain_sum` is used to create `rain_class`, so it must **not** be
    included as an input feature because this would cause target
    leakage.
-   The model predicts a rainfall category rather than an exact rainfall
    amount.
-   The rainfall thresholds above are project-defined daily classes.

**Training / testing**

-   Training: 2023--2025
-   Testing: 2026

------------------------------------------------------------------------

## Wind

**Machine Learning Model (Regression)** - Multiple Linear Regression -
simple and fast baseline for measuring the relationship between
pressure-related variables and wind speed. - Gradient Boosting
Regressor - captures nonlinear relationships between pressure, pressure
changes, wind direction, and wind speed. -
HistGradientBoostingRegressor - histogram-based gradient boosting model
designed to train efficiently on larger datasets while capturing
nonlinear relationships.

**Input (X)**

1.  `surface_pressure_mean` --- (raw)
2.  `surface_pressure_max` --- (raw)
3.  `surface_pressure_min` --- (raw)
4.  `pressure_change` --- today's mean surface pressure minus the
    previous day's mean surface pressure --- (created)
5.  `wind_direction_10m_dominant` --- (raw)

**Output (y)**

1.  `wind_speed_10m_max` --- km/h

**Status / notes**

-   MARS was removed because the required `pyearth/Earth` package is
    unavailable in the current Python environment.
-   Random Forest was not selected because it is comparatively slow and
    can create large model files for this dataset.
-   `HistGradientBoostingRegressor` is used as the more efficient third
    regression model.

**Training / testing**

-   Training: 2023--2025
-   Testing: 2026

------------------------------------------------------------------------

## LSTM - Future Input Forecasting

**Machine Learning Model (Multivariate Multi-Output Regression /
Time-Series Forecasting)** - LSTM - forecasts future daily weather
attributes that are required as inputs (X) by the downstream Rain, Wind,
Temperature, and Snow models. - This is an input-forecasting model, not
the final Rain/Wind/Temperature/Snow prediction model.

**Input (X)**

Historical sequences of the daily weather variables that need to be
forecast for the downstream models.

**Output (y)**

Future values of the required raw weather input attributes, including
the relevant:

1.  Temperature attributes
2.  Humidity / dew-point attributes
3.  Cloud-cover attributes
4.  Pressure attributes
5.  Wind attributes
6.  Solar-radiation attributes
7.  Other raw weather attributes required by the downstream models

**Created after LSTM forecasting**

-   `pressure_change` --- calculate from consecutive predicted
    `surface_pressure_mean` values rather than forecasting it
    independently.
-   `month` --- derive directly from the future forecast date.

**Purpose / flow**

`Historical weather -> LSTM -> future input attributes -> downstream ML model -> final prediction`

For example:

-   LSTM future inputs -\> Rain classifier -\> rainfall class
-   LSTM future pressure/direction -\> Wind regressor -\>
    `wind_speed_10m_max` (km/h)

------------------------------------------------------------------------

## Temp

**Machine Learning Model (Regression)** - Multiple Linear Regression -
simple and fast baseline for measuring linear relationships between the
weather attributes and maximum temperature. - Gradient Boosting
Regressor - captures nonlinear relationships between radiation,
sunshine, cloud cover, dew point, seasonality, and maximum
temperature. - HistGradientBoostingRegressor - efficient histogram-based
boosting model for larger datasets while capturing nonlinear
relationships.

**Input (X)**

1.  `shortwave_radiation_sum` --- (raw)
2.  `sunshine_duration` --- (raw)
3.  `daylight_duration` --- (raw)
4.  `cloud_cover_mean` --- daily mean --- (raw)
5.  `dew_point_2m_mean` --- daily mean --- (raw)
6.  `month` --- extracted from date --- (created)

**Output (y)**

1.  `temperature_2m_max` --- °C

**Training / testing**

-   Training: 2023--2025
-   Testing: 2026

**Status / notes**

-   The Temperature model predicts only daily maximum temperature.
-   `temperature_2m_min` is no longer a prediction target.

------------------------------------------------------------------------

## Snow

**Machine Learning Model (Regression)** - MARS - the relationship can
change around certain temperatures. MARS is made for relationships like
this because it divides the relationship into different regions. -
Random Forest Regressor - very safe - Gradient Boosting Regression

**Input (X)**

1.  `temperature_2m_min` --- (raw)
2.  `precipitation_sum` or `rain_sum` --- (raw) \[would be nice\]

**Output (y)**

1.  `snowfall_sum`

------------------------------------------------------------------------
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4

## Typhoon

**Machine Learning Model (Classification)**

-   Random Forest
-   CART / Decision Tree
-   Gradient Boosting Classifier
-   Support Vector Machine (SVM)

**Input (X)**

The current classifier uses the remaining JMA and Open-Meteo features
after leakage/unwanted columns are removed. Important retained inputs
include:

1.  `nearest_prefecture`
2.  JMA typhoon attributes such as `grade`, `pressure`, `wind_speed`,
    `indicator`, `dir_r50`, `r50_long`, `r50_short`, `dir_r30`,
    `r30_long`, `r30_short`
3.  `year`
4.  `month`
5.  `day`
6.  `openmeteo_elevation`
7.  `temperature_2m_mean`
8.  `temperature_2m_max`
9.  `temperature_2m_min`
10. `relative_humidity_2m_mean`
11. `relative_humidity_2m_max`
12. `relative_humidity_2m_min`
13. `dew_point_2m_mean`
14. `dew_point_2m_max`
15. `dew_point_2m_min`
16. `precipitation_sum`
17. `rain_sum`
18. `precipitation_hours`
19. `cloud_cover_mean`
20. `cloud_cover_max`
21. `cloud_cover_min`
22. `pressure_msl_mean`
23. `pressure_msl_max`
24. `pressure_msl_min`
25. `surface_pressure_mean`
26. `surface_pressure_max`
27. `surface_pressure_min`
28. `wind_speed_10m_mean`
29. `wind_speed_10m_max`
30. `wind_speed_10m_min`
31. `wind_gusts_10m_mean`
32. `wind_gusts_10m_max`
33. `wind_gusts_10m_min`
34. `wind_direction_10m_dominant`
35. `shortwave_radiation_sum`

<<<<<<< HEAD


=======
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
`nearest_prefecture` is retained as a categorical feature.

**Output (y)**

`risk`

<<<<<<< HEAD
1.  Low 
2.  Moderate 
3.  High 


**Training / testing**


=======
1.  Low
2.  Moderate
3.  High

**Training / testing**

>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
-   Split by `landfall_event_id` rather than individual rows to prevent
    rows from the same landfall event appearing in both sets.
-   Numeric features: missing values are median-imputed and then
    standardized with `StandardScaler`.

<<<<<<< HEAD


=======
>>>>>>> 9f54794d56652b00c1acac858c45d5ebdde021d4
**Status / notes**

-   The current target is no longer based on mapping JMA `grade`
    directly to Low/Medium/High.
-   Risk is based on the number of days before a confirmed JMA `#`
    landfall event.
-   `nearest_prefecture` is used because the intended interface allows
    the user to select a prefecture.
