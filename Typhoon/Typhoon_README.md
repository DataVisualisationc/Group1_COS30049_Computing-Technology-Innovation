# Typhoon Weather Dataset Preparation

This project prepares historical typhoon landfall data and combines it with weather conditions from the **7 days before each landfall**. The final dataset can be used for typhoon classification and machine learning.

## Files

- `bst_all.txt` : Raw JMA Best Track typhoon data. [link](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/besttrack.html) 
- `parse_bst_landfall.py`: Extracts landfall records for a selected year range.
- `landfall_2000_2025.csv`: Extracted landfall records from 2000 to 2025 so we have enough data .
- `get_weather_existing_landfall.py`: Retrieves the previous days of weather from Open-Meteo matching with the landfall 2000 - 2025. This allows us to **use the weather** from the day of landfall data "when typhoon hit japan" to **predict the next typhoon**.
- `typhoon_data_with_weather.csv` : Final dataset containing typhoon and weather data. (USE THIS for ML)

## How to Use the files

### 1. Install requirements

```bash
pip install pandas requests
```

### 2. Parse and Extract landfall data

Run:

```bash
python parse_bst_landfall.py bst_all.txt landfall_2000_2025.csv --start-year 2000 --end-year 2025
```

Change `2000` and `2025` to the year range you want.

You can also change the `landfall_2000_2025.csv` to the name you want.

This produces:

```text
landfall_2000_2025.csv
```

### 3. Retrieve weather data

Make sure `landfall_2000_2025.csv` is in the same folder, if you change the name of it, make sure to change the variable of INPUT_FILE inside `get_weather_existing_landfall.py`.

If everything matches,  run:

```bash
python get_weather_existing_landfall.py
```

The script retrieves weather data for the **7 days before each typhoon hit JAPAN** using the Open-Meteo Historical Weather API. If prior data is not recorded and landfall happen, 7 days before it will not be retrieved.

The final dataset will be saved as:

```text
typhoon_data_with_weather.csv
```

## Process

```text
bst_all.txt > parse_bst_landfall.py > landfall_2000_2025.csv > get_weather_existing_landfall.py > typhoon_data_with_weather.csv
```