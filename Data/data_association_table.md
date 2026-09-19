# Data Association Table

Reference for ML / preprocessing: which raw data fields feed into which disaster or weather output.

## 1. Disaster Outputs

| Output | Data Source | Fields Used | Notes |
|---|---|---|---|
| **Flood** | Open-Meteo (River Discharge) | `river_discharge`, `river_discharge_mean`, `river_discharge_median`, `river_discharge_max`, `river_discharge_p75`, `river_discharge_member01`–`member50` (all 50 ensemble members) | Also pull in `rain_sum (mm)` from the daily table as a supporting predictor |
| **Snow** | Open-Meteo + JMA | `snowfall_sum (cm)` (Open-Meteo, daily) | if want, can pull in JMA `snow_fall` for accuracy/validation. |
| **Typhoon** | Hui Ting's dataset + Open-Meteo | Hui Ting's dataset (typhoon-specific fields) + `wind_speed_10m_max (km/h)`, `wind_gusts_10m_max (km/h)` 

## 2. Weather-Based Design Outputs

| Output | Data Source | Fields Used |
|---|---|---|
| **Rain** | Open-Meteo (daily + hourly) | `rain_sum (mm)`, `precipitation_hours (h)`, `precipitation_sum (mm)`,`relative_humidity_2m (%)`, `cloud_cover (%)`, `weather_code` |
| **Wind** | Open-Meteo (daily) | `wind_speed_10m_max (km/h)`, `wind_gusts_10m_max (km/h)` |
| **Temp** | Open-Meteo (daily) | `temperature_2m_max (°C)`, `temperature_2m_min (°C)` |

## 3. Source Tables (Raw Schema Reference)

### River Discharge Table
`location_id`, `time`, `river_discharge`, `river_discharge_member01`–`member50`, `river_discharge_mean`, `river_discharge_median`, `river_discharge_max`, `river_discharge_p75`

### Hourly Table
`location_id`, `time`, `relative_humidity_2m (%)`, `cloud_cover (%)`, `weather_code (wmo code)`, `et0_fao_evapotranspiration (mm)`, `vapour_pressure_deficit (kPa)`


### Daily Table
`location_id`, `time`, `temperature_2m_max (°C)`, `temperature_2m_min (°C)`, `wind_speed_10m_max (km/h)`, `wind_gusts_10m_max (km/h)`, `snowfall_sum (cm)`, `rain_sum (mm)`, `precipitation_hours (h)`, `precipitation_sum (mm)`
