# Open-Meteo flood (river discharge) dataset

## What this data is

Daily river discharge data for a handful of representative towns/cities in
each of **60** Japanese prefectures (or sub-prefectural regions, in
Hokkaido's case). Each prefecture has one CSV file (e.g. `Ehime.csv`). Within
each file there are **two stacked tables**, separated by a blank line:

1. **Location table** (top, short — 4 or 5 rows)
2. **Daily river discharge table** (bottom, long — thousands of rows)

They are linked by `location_id`.

This was pulled from the **Open-Meteo Flood API**, which sources reanalysis
and forecast data from the Global Flood Awareness System (GloFAS v4, 0.05°
/ ~5 km resolution). Because of that resolution, the closest river to a given
coordinate is not always the "right" one — the API returns the largest river
found within a 5 km cell.

## Table 1: Location table

| Column                 | Meaning                                                        |
| ----------------------- | --------------------------------------------------------------- |
| `location_id`           | Primary key, links to the daily table below.                   |
| `city/town`             | Name of the representative city/town for this location.        |
| `latitude`, `longitude` | Coordinates of the grid cell actually used (may differ slightly from the requested city coordinates due to the 5 km grid). |
| `elevation`             | Elevation in meters of the grid cell.                           |
| `utc_offset_seconds`    | UTC offset in seconds (0 for all rows — data is in GMT).        |
| `timezone`, `timezone_abbreviation` | Both `GMT` for every row in this dataset.          |

Each prefecture has 4 locations, except Fukuoka, Kagoshima, Kumamoto,
Miyazaki, Nagasaki, Oita, Osaka, Saga, Shimane, Tochigi, Tokyo, Wakayama,
Yamaguchi, and Yamanashi, which have 5.

## Table 2: Daily river discharge table

| Column                             | Meaning                                                                                     |
| ----------------------------------- | --------------------------------------------------------------------------------------------- |
| `location_id`                       | Foreign key into the location table above.                                                   |
| `time`                              | Calendar date, `YYYY-MM-DD` (one row per location per day).                                  |
| `river_discharge (m³/s)`            | The single "best estimate" daily river discharge rate — the deterministic reanalysis value for older dates, or the ensemble control value for recent/forecast dates. |
| `river_discharge_member01 (m³/s)` … `river_discharge_member50 (m³/s)` | The 50 individual GloFAS ensemble forecast members. These are `NaN` until forecast ensemble data becomes available for that date (roughly mid-2023 onward — the exact cutover date varies slightly by location). |
| `river_discharge_mean (m³/s)`       | Mean of the 50 ensemble members (equals `river_discharge` when members are `NaN`).            |
| `river_discharge_median (m³/s)`     | Median of the 50 ensemble members.                                                            |
| `river_discharge_max (m³/s)`        | Maximum of the 50 ensemble members.                                                           |
| `river_discharge_p75 (m³/s)`        | 75th percentile of the 50 ensemble members.                                                   |

Each row has 57 columns total (`location_id`, `time`, `river_discharge`, 50
members, 4 summary stats). Note: unlike the API's full variable list, this
dataset does **not** include `river_discharge_min` or `river_discharge_p25`.

**⚠️ The four summary-stat columns are not in a consistent order across
files — always select by column name, never by position:**

| Variant | Files | Last 4 column order | Date range | Rows per location |
| --- | --- | --- | --- | --- |
| **A** | 35 files | `p75, mean, median, max` | 2021-01-11 → 2026-01-31 | 1,847 |
| **B** | 25 files | `mean, median, max, p75` | 2021-01-01 → 2026-01-31 | 1,857 |

Variant A files are also missing the first 10 days of 2021 (data starts
2021-01-11 instead of 2021-01-01), so they have 10 fewer rows per location
than Variant B files.

**Variant A** (p75 first; starts 2021-01-11): Aichi, Akita, Aomori, Chiba,
Fukui, Fukushima, Gifu, Gunma, Hokkaido-Hidaka, Hokkaido-Hiyama,
Hokkaido-Iburi, Hokkaido-Ishikari, Hokkaido-Kamikawa, Hokkaido-Okhotsk,
Hokkaido-Oshima, Hokkaido-Rumoi, Hokkaido-Shiribeshi, Hokkaido-Sorachi,
Hokkaido-Soya, Hokkaido-Tokachi, Ibaraki, Ishikawa, Iwate, Kanagawa, Mie,
Miyagi, Nagano, Nara, Niigata, Okayama, Osaka, Saitama, Shiga, Shizuoka,
Tottori.

**Variant B** (mean first; starts 2021-01-01): Ehime, Fukuoka, Hiroshima,
Hokkaido-Kushiro, Hokkaido-Nemuro, Hyogo, Kagawa, Kagoshima, Kochi,
Kumamoto, Kyoto, Miyazaki, Nagasaki, Oita, Okinawa, Saga, Shimane, Tochigi,
Tokushima, Tokyo, Toyama, Wakayama, Yamagata, Yamaguchi, Yamanashi.

A few files also use Windows-style CRLF line endings instead of LF
(Tochigi, Tokyo, Toyama, Wakayama, Yamagata, Yamanashi) — worth normalizing
before parsing if your tooling is line-ending-sensitive.

---

## location_id → city/town reference

_Read left to right per prefecture; `location_id` is the column position
(0-indexed). A `—` means that `location_id` does not exist for that
prefecture. This reference reflects the actual contents of the Flood.zip
files. It's mostly identical to the historical-weather dataset's
prefecture/city list, with one notable exception: **Okinawa is missing Naha**
here — its list starts at Ishigakishima (so `location_id` 0 is Ishigakishima,
not Naha as in the weather dataset), giving Okinawa only 4 locations instead
of 5._

| Prefecture            | 0                 | 1                     | 2                       | 3                     | 4                    |
| ---------------------- | ------------------ | ---------------------- | ------------------------ | ---------------------- | --------------------- |
| Aichi                  | Nagoya            | Toyohashi             | Minamichita             | Toyota                | —                    |
| Akita                  | Akita             | Oodate                | Yuzawa                  | Oga                   | —                    |
| Aomori                 | Aomori            | Hachinohe             | Hirosaki                | Mutsu                 | —                    |
| Chiba                  | Chiba             | Choushi               | Tateyama                | Narita                | —                    |
| Ehime                  | Matsuyama         | Uwajima                | Niihama                 | Imabari               | —                    |
| Fukui                  | Fukui             | Tsuruga                | Obama                   | Oono                  | —                    |
| Fukuoka                | Fukuoka (Hakata)  | Kitakyushu (Yahata)   | Kurume                  | Munakata              | Yanagawa             |
| Fukushima              | Fukushima         | Aizuwakamatsu         | Souma                   | Shirakawa             | —                    |
| Gifu                   | Gifu              | Gujo Hachiman         | Nakatsugawa             | Shirakawa-go          | —                    |
| Gunma                  | Maebashi          | Kusatsu                | Minakami                | Tatebayashi           | —                    |
| Hiroshima              | Hiroshima         | Fukuyama               | Shoubara                | Kure                  | —                    |
| Hokkaido - Hidaka      | Urakawa           | Shizunai (Shinhidaka) | Erimomisaki             | Hidakamonbetsu        | —                    |
| Hokkaido - Hiyama      | Esashi (Hiyama)   | Setana                | Okushiri Island         | Imagane               | —                    |
| Hokkaido - Iburi       | Tomakomai         | Muroran                | Date                    | Atsuma                | —                    |
| Hokkaido - Ishikari    | Sapporo           | Chitose                | Shinshinotsu            | Hamamasu              | —                    |
| Hokkaido - Kamikawa    | Asahikawa         | Furano                 | Nayoro                  | Shimukappu            | —                    |
| Hokkaido - Kushiro     | Kushiro           | Teshikaga              | Akankohan                | Shiranuka             | —                    |
| Hokkaido - Nemuro      | Nemuro            | Rausu                  | Bekkai                  | Nakashibetsu          | —                    |
| Hokkaido - Okhotsk     | Abashiri          | Kitami                 | Monbetsu                | Shari                 | —                    |
| Hokkaido - Oshima      | Hakodate          | Matsumae               | Mori                    | Kikonai               | —                    |
| Hokkaido - Rumoi       | Rumoi             | Enbetsu                | Mashike                 | Shosanbetsu           | —                    |
| Hokkaido - Shiribeshi  | Otaru             | Kutchan                | Suttsu                  | Kimobetsu             | —                    |
| Hokkaido - Sorachi     | Iwamizawa         | Takikawa               | Yubari                  | Naganuma              | —                    |
| Hokkaido - Soya        | Wakkanai          | Kafuka (Rebun Island) | Hamatonbetsu            | Esashi (Kitamiesashi) | —                    |
| Hokkaido - Tokachi     | Obihiro           | Ikeda                  | Ashoro                  | Hiroo                 | —                    |
| Hyogo                  | Kobe              | Toyooka                | Himeji                  | Sumoto (Awaji)        | —                    |
| Ibaraki                | Mito              | Hitachi                | Tsukuba                 | Kashima               | —                    |
| Ishikawa               | Kanazawa          | Suzu                   | Komatsu                 | Nanao                 | —                    |
| Iwate                  | Morioka           | Miyako                 | Ichinoseki              | Kuji                  | —                    |
| Kagawa                 | Takamatsu         | Tadotsu                | Utsumi (Higashikagawa) | Kounan (Marugame)     | —                    |
| Kagoshima              | Kagoshima         | Yakushima              | Naze (Amami)            | Makurazaki            | Ibusuki              |
| Kanagawa               | Yokohama          | Odawara                | Miura                   | Ebina                 | —                    |
| Kochi                  | Kouchi            | Murotomisaki           | Sukumo                  | Aki                   | —                    |
| Kumamoto               | Kumamoto          | Amakusa (Hondo)        | Hitoyoshi               | Aso                   | Minamata             |
| Kyoto                  | Kyoto             | Miyazu                 | Fukuchiyama             | Kyotanabe             | —                    |
| Mie                    | Tsu               | Kuwana                 | Kumano                  | Toba                  | —                    |
| Miyagi                 | Sendai            | Kesennuma              | Zao                     | Marumori              | —                    |
| Miyazaki               | Miyazaki          | Nobeoka                | Takachiho               | Kushima               | Kobayashi            |
| Nagano                 | Nagano            | Matsumoto              | Iida                    | Karuizawa             | —                    |
| Nagasaki               | Nagasaki          | Sasebo                 | Hirado                  | Tsushima (Izuhara)    | Fukue (Goto Islands) |
| Nara                   | Nara              | Gojo                   | Kamikitayama            | Uda (Oouda)           | —                    |
| Niigata                | Niigata           | Joetsu (Takada)        | Itoigawa                | Ryotsu (Sado Island)  | —                    |
| Oita                   | Oita              | Nakatsu                | Saeki                   | Hita                  | Beppu                |
| Okayama                | Okayama           | Tsuyama                | Kasaoka                 | Tamano                | —                    |
| Okinawa                | Ishigakishima     | Miyakoshima            | Nago                    | Yonagunishima         | —                    |
| Osaka                  | Osaka             | Toyonaka               | Hirakata                | Sakai                 | Kumatori             |
| Saga                   | Saga              | Karatsu                | Imari                   | Ureshino              | Tosu                 |
| Saitama                | Saitama           | Chichibu               | Kumagaya                | Koshigaya             | —                    |
| Shiga                  | Otsu              | Hikone                 | Nagahama                | Shigaraki             | —                    |
| Shimane                | Matsue            | Hamada                 | Oota                    | Izumo                 | Saigo (Oki Islands)  |
| Shizuoka               | Shizuoka          | Hamamatsu              | Atami                   | Matsuzaki             | —                    |
| Tochigi                | Utsunomiya        | Nikko                  | Nasushiobara            | Oyama                 | Ashikaga             |
| Tokushima              | Tokushima         | Ikeda (Miyoshi)        | Hiwasa                  | Kaiyou                | —                    |
| Tokyo                  | Shinjuku          | Hachioji               | Tachikawa               | Machida               | Ome                  |
| Tottori                | Tottori           | Yonago                 | Kurayoshi               | Chizu                 | —                    |
| Toyama                 | Toyama            | Takaoka                | Kurobe                  | Uozu                  | —                    |
| Wakayama               | Wakayama          | Tanabe                 | Shingu                  | Koya                  | Gobo                 |
| Yamagata               | Yamagata          | Tsuruoka               | Sakata                  | Yonezawa              | —                    |
| Yamaguchi              | Shimonoseki       | Hagi                   | Iwakuni                 | Yamaguchi             | Ube                  |
| Yamanashi              | Kofu              | Fujiyoshida            | Otsuki                  | Nirasaki              | Fujikawaguchiko      |

_(prefectures with only 4 locations simply don't have a `location_id` 4.)_
