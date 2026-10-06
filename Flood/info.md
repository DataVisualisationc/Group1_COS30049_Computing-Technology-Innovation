# Flood Risk Classification

## 1. Project Objective

The Flood component predicts a daily **flood risk level** for locations
in Japan.

Final classes: - **Low** - **Medium** - **High**

This is a classification task.

The small historical flood-event dataset is **not** the final
machine-learning training dataset. It is a reference dataset used to
study flood conditions and derive project-specific thresholds.

## 2. Overall Pipeline

``` text
Known historical flood events / GLIDE
        ↓
japan_flood_training_dataset.csv
        ↓
Retrieve/check Open-Meteo historical weather and river conditions
        ↓
Compare flood vs non-flood conditions
        ↓
Derive project-specific thresholds
        ↓
Apply conditions to individual daily Open-Meteo datasets
        ↓
Concatenate individual daily datasets
        ↓
Generate Low / Medium / High flood-risk labels
        ↓
Preprocess final large ML dataset
        ↓
2023–2025 training / 2026 testing
        ↓
CART / Gradient Boosting / ID3-style Decision Tree
```

## 3. Historical Flood Reference Dataset

Reference dataset:

``` text
japan_flood_training_dataset.csv
```

It contains: - 25 known flood examples - 25 non-flood examples - 50 rows
total

Its purpose is to compare weather and river-discharge conditions
associated with flood and non-flood cases and derive candidate
thresholds.

**Important:** This is not the final ML training dataset.

## 4. Historical Window

For each historical event, the reference builder examines the **previous
7 complete days**:

``` python
start = anchor - pd.Timedelta(days=7)
end   = anchor - pd.Timedelta(days=1)
```

The event day itself is excluded from the historical 7-day aggregation.

## 5. Data Sources

Historical flood events / GLIDE provide known flood dates and locations.

Open-Meteo historical weather provides: - `rain_sum` -
`precipitation_sum` - `precipitation_hours`

Open-Meteo Flood API provides: - `river_discharge`

Elevation is also included as a location/environmental feature.

## 6. Reference Features

``` text
rain_sum_past_3day
rain_sum_past_7day
max_daily_rain_past_7day
rain_flag_50mm
precipitation_hours_past_7day
river_discharge
river_discharge_mean_7day
river_discharge_median_7day
river_discharge_max_7day
discharge_ratio
elevation
```

### Rain features

-   `rain_sum_past_3day`: total rainfall during the previous 3 days.
-   `rain_sum_past_7day`: total rainfall during the previous 7 days.
-   `max_daily_rain_past_7day`: highest single-day rainfall during the
    previous 7 days.
-   `rain_flag_50mm`: indicates whether rainfall reached the project's
    50 mm condition.
-   `precipitation_hours_past_7day`: total precipitation hours during
    the previous 7 days.

### River features

-   `river_discharge`: river discharge associated with the evaluated
    date/location.
-   `river_discharge_mean_7day`: mean river discharge over the
    historical 7-day period.
-   `river_discharge_median_7day`: median river discharge over the
    historical 7-day period.
-   `river_discharge_max_7day`: maximum river discharge over the
    historical 7-day period.
-   `discharge_ratio`: increase in river discharge relative to its
    earlier/baseline condition.

### Location feature

-   `elevation`: elevation of the evaluated location.

## 7. Flood vs Non-Flood Comparison

  Indicator                                   Non-flood median   Flood median
  ----------------------------------------- ------------------ --------------
  Rain past 3 days                                        0.90          46.30
  Rain past 7 days                                       16.20          71.40
  Maximum daily rain previous 7 days                      9.40          36.80
  Precipitation hours previous 7 days                       24             58
  Current river discharge                                 0.94           9.47
  Mean river discharge previous 7 days                    1.14           2.64
  Median river discharge previous 7 days                  0.94           0.52
  Maximum river discharge previous 7 days                 2.56           9.47
  Discharge ratio                                        0.64x          3.14x
  Elevation                                                 80             80

The strongest differences are visible in accumulated rainfall, maximum
daily rainfall, precipitation duration, river discharge, maximum river
discharge, and discharge ratio.

## 8. Candidate Project Thresholds
I have rewrittern the treshold, this treshold is based on the Glide events matching with the Open-meteo weather. I analyzed based on there

``` text
rain_sum_past_3day             >= 46.30
rain_sum_past_7day             >= 71.40
max_daily_rain_past_7day       >= 36.80
precipitation_hours_past_7day  >= 58
river_discharge                >= 9.47
river_discharge_mean_7day      >= 2.64
river_discharge_max_7day       >= 9.47
discharge_ratio                >= 3.14
```

These are **project-derived candidate thresholds** based on the current
reference dataset. They are not official Japanese flood-warning
thresholds because I am not sure how to find. Even in theory its hard to find.

## 9. Creating the Final Daily Dataset

After deriving the flood-related conditions, they are applied to the
individual daily Open-Meteo datasets.

For each location/date, preprocessing calculates the required rolling
rainfall and river-discharge features.

The individual datasets are then concatenated into one large dataset for
ML training and testing.

Therefore:

``` text
50-row historical dataset
        ↓
derive conditions/thresholds

Daily Open-Meteo datasets
        ↓
calculate flood indicators
        ↓
apply conditions
        ↓
Low / Medium / High labels
        ↓
concatenate
        ↓
final ML dataset
```

## 10. Avoiding Future-Data Leakage

Rolling historical features must use information available **before the
day being classified**.

For example:

``` python
group["rain_sum"].shift(1).rolling(...)
```

The same principle applies to historical river-discharge features.

This prevents future/current-day information from leaking into
historical rolling features.

## 11. Flood Risk Labels

The final classes are:

``` text
Low
Medium
High
```

The current approach combines multiple rainfall and river conditions
rather than relying on one measurement.

The current Low/Medium/High rule is **project-defined** and should be
validated against the historical flood/non-flood reference examples.

## 12. Machine-Learning Split

``` text
2023–2025 → Training
2026      → Testing
```

This time-based split trains the models using historical observations
and evaluates them using later unseen observations.

For the current project, data is only required through:

``` text
2026-01-31
```

Therefore the actual testing period is:

``` text
2026-01-01 → 2026-01-31
```

Dates after January 31, 2026 are not required.

## 13. Models

The Flood component uses:

1.  **CART / Decision Tree**
2.  **Gradient Boosting**
3.  **ID3-style Decision Tree**

General model flow:

``` text
Flood-condition features
        ↓
Classification model
        ↓
Low / Medium / High
```

## 14. Important Dataset Distinction

### Reference dataset

``` text
japan_flood_training_dataset.csv
```

Used for:

``` text
Known flood/non-flood examples
→ compare conditions
→ derive candidate thresholds
```

### Final ML dataset

Created from:

``` text
Individual daily Open-Meteo datasets
→ rolling rainfall/river indicators
→ flood-risk conditions
→ Low / Medium / High labels
→ concatenate
→ train/test models
```

Do **not** describe the 50-row reference dataset as the final model
training dataset.

## 15. Current Limitations

The candidate thresholds come from a relatively small reference dataset
of 50 observations.

The Low / Medium / High labelling rule is project-defined and still
needs validation.

There is also a target-leakage consideration. If the labels are
deterministically generated from specific rainfall and river-discharge
features and those exact same features are supplied directly to the
classifier, the model may mainly learn to reproduce the labelling rule.

Model accuracy therefore needs to be interpreted together with the
method used to create the target labels.

## 16. Summary

The Flood project uses known historical flood events to identify
rainfall and river-discharge patterns associated with flooding.

The historical event dataset is a **reference for threshold
development**, while the actual machine-learning dataset comes from the
much larger daily Open-Meteo datasets.

``` text
Historical flood evidence
→ derive flood conditions
→ process daily weather + river data
→ calculate rolling indicators
→ generate Low / Medium / High risk labels
→ concatenate locations
→ train on 2023–2025
→ test on Jan 2026
→ compare CART, Gradient Boosting and ID3-style models
```
