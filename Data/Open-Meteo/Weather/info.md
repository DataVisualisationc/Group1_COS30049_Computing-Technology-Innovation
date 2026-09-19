# Open-Meteo historical weather API weather dataset

## What this data is

Daily historical weather data (Jan 1, 2021 – Jan 31, 2026, ~1,857 days) for a
handful of representative towns/cities in each of the prefacture.
Each prefecture has one CSV file (e.g. `Ehime.csv`). Within each file there are
**two stacked tables**, separated by a blank line:

1. **Location table** (top, short — 4 or 5 rows)
2. **Daily weather table** (bottom, long — thousands of rows)

They are linked by `location_id`.

## Table 2: Daily weather table

| Column                                                | Meaning                                                                                                                                                |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `location_id`                                         | Foreign key into the location table above.                                                                                                             |
| `time`                                                | Calendar date, `YYYY-MM-DD` (one row per location per day).                                                                                            |
| `temperature_2m_max (°C)` / `temperature_2m_min (°C)` | Daily max/min air temperature at 2m height.                                                                                                            |
| `wind_speed_10m_max (km/h)`                           | Daily max sustained wind speed at 10m height.                                                                                                          |
| `wind_gusts_10m_max (km/h)`                           | Daily max wind gust at 10m height.                                                                                                                     |
| `snowfall_sum (cm)`                                   | Total snowfall for the day.                                                                                                                            |
| `rain_sum (mm)`                                       | Total rainfall for the day.                                                                                                                            |
| `precipitation_hours (h)`                             | Number of hours with measurable precipitation that day. Basically means total hours of raining that day.                                               |
| `precipitation_sum (mm)`                              | Total precipitation (rain + snow water-equivalent) for the day. _However, based on the website, precipitation for this sum can also be formed by snow_ |

Each `location_id` has exactly **1,857 rows** (one per day, 2021-01-01 to
2026-01-31), so each prefecture file has 4×1,857 or 5×1,857 weather rows.

This was pulled from the **Open-Meteo historical weather API**

---

## location_id → city/town reference

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

_(some of the location like Kagawa, Kochi, and Ehime only have 4 locations, so `location_id` 4 does not
exist for those.)_
