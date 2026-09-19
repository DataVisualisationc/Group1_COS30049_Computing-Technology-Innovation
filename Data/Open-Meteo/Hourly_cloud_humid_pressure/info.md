# Open-Meteo historical weather API weather dataset

## What this data is

Historical weather data (Jan 1, 2021 – Jan 31, 2026, ~1,857 days, hourly
resolution) for a handful of representative towns/cities in each Japanese
prefecture (Hokkaido is split into its sub-regions, e.g. `Hokkaido - Kushiro`).

Each prefecture/region has one CSV file (e.g. `Ehime.csv`). Within each file
there are **two stacked tables**, separated by a blank line:

1. **Location table** (top, short — 4 or 5 rows)
2. **Hourly weather table** (bottom, long — tens of thousands of rows)

They are linked by `location_id`.

Data was pulled from the **Open-Meteo historical weather (`/v1/archive`)
API**, which reconstructs past conditions from a reanalysis dataset — a blend
of station, aircraft, buoy, radar, and satellite observations combined with
models to fill in gaps, so even locations without a nearby weather station
get an estimated record.

## Table 1: Location table

| Column                   | Meaning                                                                    |
| ------------------------ | --------------------------------------------------------------------------- |
| `location_id`             | Numeric ID for the location (0–3 or 0–4 depending on prefecture), used as the foreign key into the weather table below. |
| `city/town`               | Name of the representative city/town for this location.                    |
| `latitude` / `longitude`  | WGS84 coordinates of the grid cell used to source the weather data for this location. This can be a few km from the exact town center. |
| `elevation`               | Elevation (meters) used to statistically downscale the weather data for this location. |
| `utc_offset_seconds`      | Timezone offset applied to the `time` column in the weather table, in seconds. |
| `timezone`                | Timezone identifier (e.g. `GMT`) used for this location's data.            |
| `timezone_abbreviation`   | Short form of the timezone (e.g. `GMT`).                                    |

## Table 2: Hourly weather table

| Column                              | Meaning                                                                                                                                                  |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `location_id`                        | Foreign key into the location table above.                                                                                                                |
| `time`                               | Date and hour, ISO8601 (`YYYY-MM-DDTHH:MM`), one row per location per hour.                                                                               |
| `relative_humidity_2m (%)`           | Relative humidity at 2m above ground, at the top of the hour.                                                                                             |
| `cloud_cover (%)`                    | Total cloud cover as a fraction of the sky, at the top of the hour.                                                                                        |
| `weather_code (wmo code)`            | Numeric weather condition code for that hour, following the WMO weather interpretation codes (see table below). Derived from cloud cover, precipitation, and snowfall, not sure about thunderstorm.|
| `et0_fao_evapotranspiration (mm)`    | Reference evapotranspiration for a well-watered grass field over the preceding hour, basically base water loss from the crop and surrounding air. |
| `vapour_pressure_deficit (kPa)`      | Vapor pressure deficit at the top of the hour. Above ~1.6 kPa, plant water transpiration increases; below ~0.4 kPa, it decreases.                          |

Each `location_id` has **44,568 rows** (24 hours × ~1,857 days, 2021-01-01T00:00
through 2026-01-31T23:00), so each file has 4×44,568 or 5×44,568 weather rows.

### WMO weather interpretation codes

| Code       | Description                                       |
| ---------- | -------------------------------------------------- |
| 0          | Clear sky                                          |
| 1, 2, 3    | Mainly clear, partly cloudy, overcast              |
| 45, 48     | Fog and depositing rime fog                        |
| 51, 53, 55 | Drizzle: light, moderate, dense                    |
| 56, 57     | Freezing drizzle: light, dense                     |
| 61, 63, 65 | Rain: slight, moderate, heavy                      |
| 66, 67     | Freezing rain: light, heavy                        |
| 71, 73, 75 | Snowfall: slight, moderate, heavy                  |
| 77         | Snow grains                                        |
| 80, 81, 82 | Rain showers: slight, moderate, violent            |
| 85, 86     | Snow showers: slight, heavy                        |
| 95*        | Thunderstorm: slight or moderate                   |
| 96, 99*    | Thunderstorm with slight or heavy hail             |

\* Thunderstorm-with-hail codes are only meaningful for Central Europe in
Open-Meteo's model, so treat them cautiously for this Japan dataset.

---

## location_id → city/town reference

This is now included directly as the `city/town` column in each file's
location table, but is kept here as a quick-reference lookup.

| Prefecture            | 0                | 1                     | 2                      | 3                     | 4                    |
| --------------------- | ---------------- | --------------------- | ---------------------- | --------------------- | -------------------- |
| Yamaguchi             | Shimonoseki      | Hagi                  | Iwakuni                | Yamaguchi             | Ube                  |
| Miyazaki              | Miyazaki         | Nobeoka               | Takachiho              | Kushima               | Kobayashi            |
| Kagoshima             | Kagoshima        | Yakushima             | Naze (Amami)           | Makurazaki            | Ibusuki              |
| Oita                  | Oita             | Nakatsu               | Saeki                  | Hita                  | Beppu                |
| Fukuoka               | Fukuoka (Hakata) | Kitakyushu (Yahata)   | Kurume                 | Munakata              | Yanagawa             |
| Kumamoto              | Kumamoto         | Amakusa (Hondo)       | Hitoyoshi              | Aso                   | Minamata             |
| Saga                  | Saga             | Karatsu               | Imari                  | Ureshino              | Tosu                 |
| Nagasaki              | Nagasaki         | Sasebo                | Hirado                 | Tsushima (Izuhara)    | Fukue (Goto Islands) |
| Okinawa               | Naha             | Ishigakishima         | Miyakoshima            | Nago                  | Yonagunishima        |
| Shimane               | Matsue           | Hamada                | Oota                   | Izumo                 | Saigo (Oki Islands)  |
| Kagawa                | Takamatsu        | Tadotsu               | Utsumi (Higashikagawa) | Kounan (Marugame)     | —                    |
| Kochi                 | Kouchi           | Murotomisaki          | Sukumo                 | Aki                   | —                    |
| Ehime                 | Matsuyama        | Uwajima               | Niihama                | Imabari               | —                    |
| Kyoto                 | Kyoto            | Miyazu                | Fukuchiyama            | Kyotanabe             | —                    |
| Hyogo                 | Kobe             | Toyooka               | Himeji                 | Sumoto (Awaji)        | —                    |
| Tokushima             | Tokushima        | Ikeda (Miyoshi)       | Hiwasa                 | Kaiyou                | —                    |
| Tottori               | Tottori          | Yonago                | Kurayoshi              | Chizu                 | —                    |
| Okayama               | Okayama          | Tsuyama               | Kasaoka                | Tamano                | —                    |
| Hiroshima             | Hiroshima        | Fukuyama              | Shoubara               | Kure                  | —                    |
| Gifu                  | Gifu             | Gujo Hachiman         | Nakatsugawa            | Shirakawa-go          | —                    |
| Gunma                 | Maebashi         | Kusatsu               | Minakami               | Tatebayashi           | —                    |
| Osaka                 | Osaka            | Toyonaka              | Hirakata               | Sakai                 | Kumatori             |
| Aichi                 | Nagoya           | Toyohashi             | Minamichita            | Toyota                | —                    |
| Chiba                 | Chiba            | Choushi               | Tateyama               | Narita                | —                    |
| Aomori                | Aomori           | Hachinohe             | Hirosaki               | Mutsu                 | —                    |
| Akita                 | Akita            | Oodate                | Yuzawa                 | Oga                   | —                    |
| Fukushima             | Fukushima        | Aizuwakamatsu         | Souma                  | Shirakawa             | —                    |
| Ibaraki               | Mito             | Hitachi               | Tsukuba                | Kashima               | —                    |
| Ishikawa              | Kanazawa         | Suzu                  | Komatsu                | Nanao                 | —                    |
| Fukui                 | Fukui            | Tsuruga               | Obama                  | Oono                  | —                    |
| Kanagawa              | Yokohama         | Odawara               | Miura                  | Ebina                 | —                    |
| Iwate                 | Morioka          | Miyako                | Ichinoseki             | Kuji                  | —                    |
| Miyagi                | Sendai           | Kesennuma             | Zao                    | Marumori              | —                    |
| Saitama               | Saitama          | Chichibu              | Kumagaya               | Koshigaya             | —                    |
| Nara                  | Nara             | Gojo                  | Kamikitayama           | Uda (Oouda)           | —                    |
| Shizuoka              | Shizuoka         | Hamamatsu             | Atami                  | Matsuzaki             | —                    |
| Shiga                 | Otsu             | Hikone                | Nagahama               | Shigaraki             | —                    |
| Mie                   | Tsu              | Kuwana                | Kumano                 | Toba                  | —                    |
| Hokkaido - Ishikari   | Sapporo          | Chitose               | Shinshinotsu           | Hamamasu              | —                    |
| Hokkaido - Shiribeshi | Otaru            | Kutchan               | Suttsu                 | Kimobetsu             | —                    |
| Hokkaido - Oshima     | Hakodate         | Matsumae              | Mori                   | Kikonai               | —                    |
| Hokkaido - Soya       | Wakkanai         | Kafuka (Rebun Island) | Hamatonbetsu           | Esashi (Kitamiesashi) | —                    |
| Hokkaido - Kamikawa   | Asahikawa        | Furano                | Nayoro                 | Shimukappu            | —                    |
| Hokkaido - Hidaka     | Urakawa          | Shizunai (Shinhidaka) | Erimomisaki            | Hidakamonbetsu        | —                    |
| Hokkaido - Rumoi      | Rumoi            | Enbetsu               | Mashike                | Shosanbetsu           | —                    |
| Hokkaido - Sorachi    | Iwamizawa        | Takikawa              | Yubari                 | Naganuma              | —                    |
| Hokkaido - Iburi      | Tomakomai        | Muroran               | Date                   | Atsuma                | —                    |
| Hokkaido - Hiyama     | Esashi (Hiyama)  | Setana                | Okushiri Island        | Imagane               | —                    |
| Hokkaido - Tokachi    | Obihiro          | Ikeda                 | Ashoro                 | Hiroo                 | —                    |
| Hokkaido - Okhotsk    | Abashiri         | Kitami                | Monbetsu               | Shari                 | —                    |
| Hokkaido - Nemuro     | Nemuro           | Rausu                 | Bekkai                 | Nakashibetsu          | —                    |
| Hokkaido - Kushiro    | Kushiro          | Teshikaga             | Akankohan              | Shiranuka             | —                    |
| Toyama                | Toyama           | Takaoka               | Kurobe                 | Uozu                  | —                    |
| Yamanashi             | Kofu             | Fujiyoshida           | Otsuki                 | Nirasaki              | Fujikawaguchiko      |
| Wakayama              | Wakayama         | Tanabe                | Shingu                 | Koya                  | Gobo                 |
| Tokyo                 | Shinjuku         | Hachioji              | Tachikawa              | Machida               | Ome                  |
| Yamagata              | Yamagata         | Tsuruoka              | Sakata                 | Yonezawa              | —                    |
| Tochigi               | Utsunomiya       | Nikko                 | Nasushiobara           | Oyama                 | Ashikaga             |

_(Kagawa, Kochi, and Ehime only have 4 locations, so `location_id` 4 does not
exist for those.)_

---

## Data source notes

- Pulled from Open-Meteo's `/v1/archive` historical weather endpoint, which
  covers 1940–present depending on the underlying reanalysis dataset.
- Reanalysis datasets combine real observations (stations, aircraft, buoys,
  radar, satellite) with models to fill spatial/temporal gaps, so even
  locations without a nearby station get an estimated record. Spatial
  resolution for the historical archive is roughly 9 km, fine enough to
  resolve most coastal and mountain terrain features.
- We will continue collecting more variables/locations as API request
  limits reset.

## Citation

If citing this data, credit Open-Meteo and the underlying reanalysis
sources:

- Zippenfenig, P. (2023). *Open-Meteo.com Weather API* [Computer software]. Zenodo. https://doi.org/10.5281/ZENODO.7970649
- Hersbach, H. et al. (2023). *ERA5 hourly data on single levels from 1940 to present* [Data set]. ECMWF. https://doi.org/10.24381/cds.adbb2d47
- Muñoz Sabater, J. (2019). *ERA5-Land hourly data from 2001 to present* [Data set]. ECMWF. https://doi.org/10.24381/CDS.E2161BAC
- Schimanke, S. et al. (2021). *CERRA sub-daily regional reanalysis data for Europe on single levels from 1984 to present* [Data set]. ECMWF. https://doi.org/10.24381/CDS.622A565A
- Generated using Copernicus Climate Change Service information, 2022.
