# Japan Meteorological Agency (JMA) 


Files were downloaded from JMA in Japanese (Shift-JIS encoded).
Every file in this dataset has been translated to English.

## File naming

Files are generally named `<prefecture>_<data type>[_pN].csv`, e.g.:

- `fukuoka_snow_fall.csv` — Fukuoka prefecture, snowfall
- `kagoshima_min_max_temp_p2.csv` — Kagoshima prefecture, min/max temp, part 2 of a multi-part download

Some prefectures required multiple files (`p1`, `p2`, `p3`) because JMA caps
the number of stations/columns per single download. 

## CSV structure

Every file follows the same layout as JMA's original export format:

| Row | Content |
|---|---|
| 1 | `Downloaded at: <timestamp>` |
| 2 | (blank) |
| 3 | Station name (romanized), repeated once per column belonging to that station |
| 4 | Item name — `Date`, `Total snowfall (cm)`, `Max temperature (℃)`, or `Min temperature (℃)` |
| 5 | (blank spacer row) |
| 6 | Sub-labels — `Quality info`, `Homogeneity no.`, and (snowfall files only) `No-phenomenon info` |
| 7+ | Data rows, one per date |

Each station occupies a block of 3–4 columns: the observed value, followed by
its quality info / homogeneity number / (for snowfall) no-phenomenon flag.

## Column meanings

**Quality info** — indicates how reliable the value is:

| Value | Meaning |
|---|---|
| 8 | Normal value (no missing data used in the statistic) |
| 5 | Near-normal value (missing data within an acceptable range, ~80% completeness) |
| 4 | Data deficiency (missing data beyond the acceptable range) |
| 2 | Doubtful value (hourly values only) |
| 1 | Missing — no statistical data available |
| 0 | Not an observational/statistical item (e.g. a reference value) |

**No-phenomenon info** (snowfall files only) — whether the phenomenon
(snowfall) was observed at all:

| Value | Meaning |
|---|---|
| 1 | No phenomenon occurred (e.g. no snow that day) |
| 0 | Phenomenon was observed |

So far that is what we know based on the website page.

## Station names

Station names were originally in Japanese (kanji/kana) and have been
romanized (converted to English letters) using automated kanji-to-romaji
conversion. Translator was used to translate too.


## Coverage

116 files across the following prefectures/regions:

Aichi, Akita, Aomori, Chiba, Ehime, Fukui, Fukuoka, Fukushima, Gifu, Gunma,
Hiroshima, Hyogo, Ibaraki, Ishikawa, Iwate, Kagawa, Kagoshima, Kanagawa,
Kochi, Kumamoto, Kyoto, Mie, Miyagi, Miyazaki, Nagano, Nagasaki, Nara,
Niigata, Oita, Okayama, Okinawa, Osaka, Saga, Saitama, Shiga, Shimane,
Shizuoka, Tochigi, Tokushima, Tokyo, Tottori, Toyama, Wakayama, Yamagata,
Yamaguchi, Yamanashi, and Hokkaido (Soya, Kamikawa, Okhotsk, Rumoi,
Ishikari, Shiribeshi, Iburi, Hidaka, Oshima, Hiyama, Tokachi, Kushiro,
Nemuro).

Snowfall data covers Kyushu, Chugoku, and Shikoku prefectures plus Okinawa;
min/max temperature data covers all of Japan's prefectures.

