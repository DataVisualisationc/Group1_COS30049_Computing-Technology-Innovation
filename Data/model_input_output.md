# Model Input / Output Reference

Reference for preprocessing: each model's input (X) and output (y) fields, and which fields are raw data pulls vs. features engineered by us.

Legend: **(raw)** = pulled directly from Open-Meteo / source dataset — **(created)** = engineered by us in preprocessing.

---

## Flood

**Input (X)**

1. `river_discharge`, `river_discharge_mean`, `river_discharge_median`, `river_discharge_max` — (raw)
2. `rain_sum_past_3day` — rolling 3-day sum of `rain_sum` — (created)
3. `rain_flag_50mm` — flag for any day where `rain_sum` > 50mm — (created)
4. `discharge_ratio` — flag for when `river_discharge` has tripled (3x) relative to its value 4 days prior — (created)
5. `elevation` — (raw, from location table)

**Output (y)**
Flood occurrence severity — 3-level flag:

1. Low
2. Medium
3. High

---

## Rain

**Input (X)**

1. `relative_humidity_2m` — hourly, aggregate to daily (mean) — (raw)
2. `cloud_cover` — hourly, aggregate to daily (mean) — (raw)
3. `weather_code` — hourly, needs a daily conversion method — (raw, aggregation TBD)

**Output (y)**

1. `rain_sum`
2. `precipitation_sum`
3. `precipitation_hours`

**Status / notes**

- `weather_code` is categorical (WMO codes) — averaging doesn't work. Use daily mode, or a derived proportion (e.g., % of hours reporting rain-type codes) instead.
- `rain_sum` and `precipitation_sum` will be highly correlated (precipitation = rain + snow) — check for redundancy before treating as 3 independent targets.

---

## Wind

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

**Input (X)**

1. `temperature_2m_min` — (raw)
2. `precipitation_sum` or `rain_sum` — (raw) [would be nice]

**Output (y)**

1. `snowfall_sum`

---

## Typhoon

still thinking whether we should do classification of all hit cities and predict based on that or like maybe we straight away predict the next location of the typhoon
