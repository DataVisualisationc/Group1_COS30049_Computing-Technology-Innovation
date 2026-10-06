import os
import time
import requests
import pandas as pd
from pathlib import Path

# ============================================================
# OPEN-METEO DAILY WEATHER DOWNLOADER
# Input : jma_day3_to_landfall_before_weather.csv
# Output: jma_day3_to_landfall_with_weather.csv
#
# - Uses ALL rows, including incomplete sequences.
# - Downloads one daily weather record per JMA row.
# - Resumable: saves progress after every successful row.
# - Rerun the script after interruption; completed rows are skipped.
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

INPUT_FILE = PROCESSED / "jma_day3_to_landfall_before_weather.csv"
PROGRESS_FILE = PROCESSED / "jma_openmeteo_daily_progress.csv"
OUTPUT_FILE = PROCESSED / "jma_day3_to_landfall_with_weather.csv"

API_URL = "https://archive-api.open-meteo.com/v1/archive"

TIMEZONE = "Asia/Tokyo"

DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",

    "relative_humidity_2m_mean",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",

    "dew_point_2m_mean",
    "dew_point_2m_max",
    "dew_point_2m_min",

    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",

    "cloud_cover_mean",
    "cloud_cover_max",
    "cloud_cover_min",

    "pressure_msl_mean",
    "pressure_msl_max",
    "pressure_msl_min",

    "surface_pressure_mean",
    "surface_pressure_max",
    "surface_pressure_min",

    "wind_speed_10m_mean",
    "wind_speed_10m_max",
    "wind_speed_10m_min",

    "wind_gusts_10m_mean",
    "wind_gusts_10m_max",
    "wind_gusts_10m_min",

    "wind_direction_10m_dominant",
    "shortwave_radiation_sum",
]

# Be polite to the public API.
REQUEST_DELAY_SECONDS = 0.35
MAX_RETRIES = 6
TIMEOUT_SECONDS = 60


def make_row_key(row):
    """
    Unique key for a landfall event + relative day.
    This remains unique even when the same storm has multiple landfalls.
    """
    return (
        str(row["landfall_event_id"])
        + "|"
        + str(int(row["days_before_landfall"]))
    )


def fetch_daily_weather(session, latitude, longitude, date_string):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_string,
        "end_date": date_string,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": TIMEZONE,
        # Important for typhoons: use the nearest grid cell rather than
        # forcing an offshore storm point onto a land grid cell.
        "cell_selection": "nearest",
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                API_URL,
                params=params,
                timeout=TIMEOUT_SECONDS,
            )

            if response.status_code == 429:
                wait = min(60, 5 * attempt)
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            payload = response.json()

            if payload.get("error"):
                raise RuntimeError(payload.get("reason", "Unknown API error"))

            daily = payload.get("daily", {})

            if not daily.get("time"):
                raise RuntimeError("API returned no daily weather row.")

            weather = {}

            for variable in DAILY_VARIABLES:
                values = daily.get(variable)

                if values and len(values) > 0:
                    weather[variable] = values[0]
                else:
                    weather[variable] = None

            # Metadata describing the actual Open-Meteo grid point.
            weather["openmeteo_latitude"] = payload.get("latitude")
            weather["openmeteo_longitude"] = payload.get("longitude")
            weather["openmeteo_elevation"] = payload.get("elevation")
            weather["openmeteo_timezone"] = payload.get("timezone")
            weather["weather_download_status"] = "complete"
            weather["weather_error"] = ""

            return weather

        except Exception as exc:
            last_error = str(exc)

            if attempt < MAX_RETRIES:
                wait = min(30, 2 ** attempt)
                print(
                    f"  Attempt {attempt}/{MAX_RETRIES} failed: "
                    f"{last_error}"
                )
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)

    return {
        **{variable: None for variable in DAILY_VARIABLES},
        "openmeteo_latitude": None,
        "openmeteo_longitude": None,
        "openmeteo_elevation": None,
        "openmeteo_timezone": None,
        "weather_download_status": "failed",
        "weather_error": last_error,
    }


def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return pd.DataFrame()

    try:
        progress = pd.read_csv(PROGRESS_FILE)
        print(f"Existing progress rows: {len(progress)}")
        return progress
    except Exception as exc:
        print(f"Could not read progress file: {exc}")
        return pd.DataFrame()


def save_progress(records):
    pd.DataFrame(records).to_csv(
        PROGRESS_FILE,
        index=False
    )


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE}. "
            "Put this script in the same folder as the JMA CSV."
        )

    source = pd.read_csv(INPUT_FILE)

    required = {
        "landfall_event_id",
        "days_before_landfall",
        "date",
        "latitude",
        "longitude",
    }

    missing = required - set(source.columns)

    if missing:
        raise KeyError(
            f"Input CSV is missing required columns: {sorted(missing)}"
        )

    source["row_key"] = source.apply(make_row_key, axis=1)

    if source["row_key"].duplicated().any():
        dupes = source.loc[
            source["row_key"].duplicated(keep=False),
            ["row_key", "storm_name", "date"]
        ]

        raise ValueError(
            "Duplicate event/day keys detected:\n"
            + dupes.head(20).to_string(index=False)
        )

    progress = load_progress()

    # Store only weather/progress fields in the progress file.
    progress_records = (
        progress.to_dict("records")
        if not progress.empty
        else []
    )

    completed_keys = set()

    if not progress.empty and "row_key" in progress.columns:
        complete_mask = (
            progress["weather_download_status"]
            .eq("complete")
        )

        completed_keys = set(
            progress.loc[complete_mask, "row_key"].astype(str)
        )

    print("\n" + "=" * 65)
    print("OPEN-METEO DAILY WEATHER DOWNLOAD")
    print("=" * 65)
    print(f"Input rows           : {len(source)}")
    print(f"Already complete     : {len(completed_keys)}")
    print(f"Still to download    : {len(source) - len(completed_keys)}")
    print(f"Timezone             : {TIMEZONE}")
    print(f"Daily variables      : {len(DAILY_VARIABLES)}")
    print("=" * 65)

    # For replacing failed progress rows after a successful retry.
    progress_by_key = {
        str(r.get("row_key")): r
        for r in progress_records
        if r.get("row_key") is not None
    }

    session = requests.Session()
    session.headers.update({
        "User-Agent": "JMA-landfall-research-dataset/1.0"
    })

    total = len(source)

    for position, row in source.iterrows():
        key = str(row["row_key"])

        if key in completed_keys:
            continue

        date_string = pd.to_datetime(
            row["date"]
        ).strftime("%Y-%m-%d")

        print(
            f"[{position + 1}/{total}] "
            f"{row.get('storm_name', '')} | "
            f"{row.get('relative_day', '')} | "
            f"{date_string} | "
            f"{float(row['latitude']):.2f}, "
            f"{float(row['longitude']):.2f}"
        )

        weather = fetch_daily_weather(
            session=session,
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            date_string=date_string,
        )

        progress_row = {
            "row_key": key,
            "landfall_event_id": row["landfall_event_id"],
            "days_before_landfall": row["days_before_landfall"],
            "date": date_string,
            "requested_latitude": row["latitude"],
            "requested_longitude": row["longitude"],
            **weather,
        }

        progress_by_key[key] = progress_row

        # Save after EVERY request so interruption loses at most one row.
        save_progress(
            list(progress_by_key.values())
        )

        if weather["weather_download_status"] == "complete":
            completed_keys.add(key)
            print("  -> complete")
        else:
            print(
                "  -> FAILED:",
                weather["weather_error"]
            )

        time.sleep(REQUEST_DELAY_SECONDS)

    # ========================================================
    # FINAL MERGE
    # ========================================================

    progress = pd.read_csv(PROGRESS_FILE)

    weather_columns = [
        "row_key",
        *DAILY_VARIABLES,
        "openmeteo_latitude",
        "openmeteo_longitude",
        "openmeteo_elevation",
        "openmeteo_timezone",
        "weather_download_status",
        "weather_error",
    ]

    final = source.merge(
        progress[weather_columns],
        on="row_key",
        how="left",
        validate="one_to_one",
    )

    final.to_csv(
        OUTPUT_FILE,
        index=False
    )

    complete = (
        final["weather_download_status"]
        .eq("complete")
        .sum()
    )

    failed = (
        final["weather_download_status"]
        .eq("failed")
        .sum()
    )

    missing_weather = (
        final["weather_download_status"]
        .isna()
        .sum()
    )

    print("\n" + "=" * 65)
    print("DOWNLOAD STATUS")
    print("=" * 65)
    print(f"Input rows       : {len(final)}")
    print(f"Complete weather : {complete}")
    print(f"Failed weather   : {failed}")
    print(f"Not downloaded   : {missing_weather}")
    print(f"Progress file    : {PROGRESS_FILE}")
    print(f"Final dataset    : {OUTPUT_FILE}")

    if complete == len(final):
        print("\nAll 788-style sequence rows have weather data.")
    else:
        print(
            "\nSome rows are incomplete. "
            "Run this script again to retry them."
        )


if __name__ == "__main__":
    main()
