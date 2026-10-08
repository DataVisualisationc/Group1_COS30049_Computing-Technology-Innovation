import os
import time
import requests
import pandas as pd

# ============================================================
# SETTINGS
# ============================================================

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))

COORDINATES_FILE = os.path.join(
    SCRIPT_FOLDER,
    "japan_towns_coordinates.csv"
)

OUTPUT_FOLDER = os.path.join(
    SCRIPT_FOLDER,
    "Missing_weather_dataset"
)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

START_DATE = "2021-01-01"
END_DATE = "2026-01-31"
TIMEZONE = "Asia/Tokyo"

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

MAX_RETRIES = 5
REQUEST_TIMEOUT = 120
SLEEP_BETWEEN_REQUESTS = 1.0


# ============================================================
# SPLIT THE 15 MISSING FEATURES INTO TWO API REQUESTS
# ============================================================

FEATURE_GROUPS = {
    "group_1_temperature_humidity_cloud": [
        "temperature_2m_mean",

        "relative_humidity_2m_mean",
        "relative_humidity_2m_max",
        "relative_humidity_2m_min",

        "dew_point_2m_min",

        "cloud_cover_mean",
        "cloud_cover_max",
        "cloud_cover_min",
    ],

    "group_2_pressure_wind": [
        "pressure_msl_mean",
        "pressure_msl_max",
        "pressure_msl_min",

        "wind_speed_10m_mean",
        "wind_speed_10m_min",

        "wind_gusts_10m_mean",
        "wind_gusts_10m_min",
    ],
}


# ============================================================
# PATHS FOR EACH GROUP
# ============================================================

def group_paths(group_name):
    return {
        "data": os.path.join(
            OUTPUT_FOLDER,
            f"{group_name}_2021_2026.csv"
        ),
        "progress": os.path.join(
            OUTPUT_FOLDER,
            f"{group_name}_progress.csv"
        ),
        "failed": os.path.join(
            OUTPUT_FOLDER,
            f"{group_name}_failed.csv"
        ),
    }


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def make_town_key(prefecture, town, latitude, longitude):
    return (
        f"{clean_text(prefecture)}|"
        f"{clean_text(town)}|"
        f"{float(latitude):.6f}|"
        f"{float(longitude):.6f}"
    )


def append_row(path, record):
    df = pd.DataFrame([record])
    exists = os.path.exists(path)

    df.to_csv(
        path,
        mode="a",
        header=not exists,
        index=False,
        encoding="utf-8-sig"
    )


def load_completed_keys(progress_file):
    if not os.path.exists(progress_file):
        return set()

    # Try the common encodings used by the progress files.
    for encoding in ["utf-8-sig", "utf-16"]:
        try:
            progress = pd.read_csv(
                progress_file,
                encoding=encoding
            )

            if "town_key" not in progress.columns:
                return set()

            if "status" not in progress.columns:
                return set()

            completed = progress[
                progress["status"]
                .astype(str)
                .str.lower()
                .eq("complete")
            ]

            return set(
                completed["town_key"].astype(str)
            )

        except UnicodeError:
            # Try the next encoding
            continue

        except Exception as exc:
            print(
                f"WARNING: Could not read {progress_file}: {exc}"
            )
            return set()

    print(
        f"WARNING: Could not determine encoding for {progress_file}"
    )
    return set()

# ============================================================
# OPEN-METEO REQUEST
# ============================================================

def request_weather(latitude, longitude, variables):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(variables),
        "timezone": TIMEZONE,
        "cell_selection": "nearest",
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                ARCHIVE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            # ------------------------------------------------
            # IMPORTANT: show Open-Meteo's actual 400 reason
            # ------------------------------------------------
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    reason = error_data.get(
                        "reason",
                        str(error_data)
                    )
                except Exception:
                    reason = response.text

                # A 400 is a bad request, so retrying the exact
                # same URL will not fix it.
                raise ValueError(
                    "Open-Meteo rejected this request.\n"
                    f"Reason: {reason}\n"
                    f"URL: {response.url}"
                )

            # ------------------------------------------------
            # Retry only temporary errors
            # ------------------------------------------------
            if (
                response.status_code == 429
                or response.status_code >= 500
            ):
                wait = min(60, 2 ** attempt)

                print(
                    f"    Temporary HTTP {response.status_code}. "
                    f"Retrying in {wait}s..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                raise ValueError(
                    "Open-Meteo error: "
                    + str(data.get("reason"))
                )

            if (
                "daily" not in data
                or "time" not in data["daily"]
            ):
                raise RuntimeError(
                    "Response did not contain daily data."
                )

            return data

        except ValueError:
            # Permanent request problem. Do not waste time retrying.
            raise

        except Exception as exc:
            last_error = exc

            if attempt < MAX_RETRIES:
                wait = min(60, 2 ** attempt)

                print(
                    f"    Temporary failure "
                    f"({attempt}/{MAX_RETRIES}): {exc}"
                )
                print(
                    f"    Retrying in {wait}s..."
                )

                time.sleep(wait)

    raise RuntimeError(
        f"Request failed after {MAX_RETRIES} attempts: "
        f"{last_error}"
    )


# ============================================================
# RESPONSE -> DATAFRAME
# ============================================================

def response_to_dataframe(
    data,
    variables,
    source_index,
    prefecture,
    town,
    latitude,
    longitude
):
    daily = data["daily"]

    result = pd.DataFrame({
        "date": daily["time"]
    })

    for variable in variables:
        if variable in daily:
            result[variable] = daily[variable]
        else:
            result[variable] = pd.NA

    result.insert(0, "source_index", source_index)
    result.insert(1, "prefecture", prefecture)
    result.insert(2, "town", town)
    result.insert(3, "latitude", latitude)
    result.insert(4, "longitude", longitude)

    result["openmeteo_latitude"] = data.get("latitude")
    result["openmeteo_longitude"] = data.get("longitude")
    result["openmeteo_elevation"] = data.get("elevation")
    result["openmeteo_timezone"] = data.get("timezone")
    result["utc_offset_seconds"] = data.get(
        "utc_offset_seconds"
    )

    dates = pd.to_datetime(result["date"])

    result["year"] = dates.dt.year
    result["month"] = dates.dt.month
    result["day"] = dates.dt.day

    first_columns = [
        "source_index",
        "prefecture",
        "town",
        "latitude",
        "longitude",
        "openmeteo_latitude",
        "openmeteo_longitude",
        "openmeteo_elevation",
        "openmeteo_timezone",
        "utc_offset_seconds",
        "date",
        "year",
        "month",
        "day",
    ]

    return result[
        first_columns + variables
    ]


# ============================================================
# DOWNLOAD ONE FEATURE GROUP
# ============================================================

def download_group(
    towns,
    group_number,
    group_name,
    variables
):
    paths = group_paths(group_name)

    completed_keys = load_completed_keys(
        paths["progress"]
    )

    remaining = 0

    for _, row in towns.iterrows():
        key = make_town_key(
            row["Prefecture/Region"],
            row["Town"],
            row["Latitude"],
            row["Longitude"]
        )

        if key not in completed_keys:
            remaining += 1

    print()
    print("=" * 72)
    print(
        f"API GROUP {group_number}: {group_name}"
    )
    print("=" * 72)

    print("Features:")

    for variable in variables:
        print("  -", variable)

    print()
    print("Already complete :", len(completed_keys))
    print("Still remaining   :", remaining)
    print("Output            :", paths["data"])

    if remaining == 0:
        print(
            "\nThis feature group is already complete."
        )
        return

    output_exists = os.path.exists(
        paths["data"]
    )

    success = 0
    failed = 0

    for position, (_, row) in enumerate(
        towns.iterrows(),
        start=1
    ):
        source_index = (
            row["Index"]
            if "Index" in towns.columns
            else position - 1
        )

        prefecture = clean_text(
            row["Prefecture/Region"]
        )

        town = clean_text(
            row["Town"]
        )

        latitude = float(
            row["Latitude"]
        )

        longitude = float(
            row["Longitude"]
        )

        key = make_town_key(
            prefecture,
            town,
            latitude,
            longitude
        )

        if key in completed_keys:
            print(
                f"[{position}/{len(towns)}] "
                f"SKIP {prefecture} / {town}"
            )
            continue

        print(
            f"\n[{position}/{len(towns)}] "
            f"{prefecture} / {town}"
        )

        try:
            data = request_weather(
                latitude,
                longitude,
                variables
            )

            result = response_to_dataframe(
                data=data,
                variables=variables,
                source_index=source_index,
                prefecture=prefecture,
                town=town,
                latitude=latitude,
                longitude=longitude
            )

            result.to_csv(
                paths["data"],
                mode="a",
                header=not output_exists,
                index=False,
                encoding="utf-8-sig"
            )

            output_exists = True

            append_row(
                paths["progress"],
                {
                    "town_key": key,
                    "source_index": source_index,
                    "prefecture": prefecture,
                    "town": town,
                    "latitude": latitude,
                    "longitude": longitude,
                    "status": "complete",
                    "rows_downloaded": len(result),
                    "start_date": START_DATE,
                    "end_date": END_DATE,
                    "error": "",
                }
            )

            completed_keys.add(key)
            success += 1

            print(
                f"  COMPLETE: {len(result)} rows"
            )

        except Exception as exc:
            failed += 1

            error_message = str(exc)

            print("  FAILED:")
            print(" ", error_message)

            append_row(
                paths["progress"],
                {
                    "town_key": key,
                    "source_index": source_index,
                    "prefecture": prefecture,
                    "town": town,
                    "latitude": latitude,
                    "longitude": longitude,
                    "status": "failed",
                    "rows_downloaded": 0,
                    "start_date": START_DATE,
                    "end_date": END_DATE,
                    "error": error_message,
                }
            )

            append_row(
                paths["failed"],
                {
                    "town_key": key,
                    "source_index": source_index,
                    "prefecture": prefecture,
                    "town": town,
                    "latitude": latitude,
                    "longitude": longitude,
                    "error": error_message,
                }
            )

            # If the first request itself is invalid, continuing
            # through all 255 towns would just generate 255 copies
            # of the same error.
            if position == 1 and "rejected this request" in error_message:
                print(
                    "\nSTOPPING THIS GROUP because Open-Meteo "
                    "rejected the request itself."
                )
                print(
                    "Fix the reported API reason before continuing."
                )
                return

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print()
    print("-" * 72)
    print(
        f"{group_name} FINISHED"
    )
    print("-" * 72)
    print("Successful this run :", success)
    print("Failed this run     :", failed)
    print("Total complete      :", len(completed_keys))
    print("Expected towns      :", len(towns))


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("JAPAN MISSING DAILY WEATHER DOWNLOADER - SPLIT VERSION")
    print("=" * 72)

    print()
    print("Input:")
    print(COORDINATES_FILE)

    print()
    print("Output folder:")
    print(OUTPUT_FOLDER)

    print()
    print(
        f"Date range: {START_DATE} -> {END_DATE}"
    )

    if not os.path.exists(COORDINATES_FILE):
        raise FileNotFoundError(
            "\nCould not find:\n"
            f"{COORDINATES_FILE}\n\n"
            "Put japan_towns_coordinates.csv in the "
            "same folder as this script."
        )

    towns = pd.read_csv(
        COORDINATES_FILE
    )

    required = [
        "Prefecture/Region",
        "Town",
        "Latitude",
        "Longitude",
    ]

    missing = [
        column
        for column in required
        if column not in towns.columns
    ]

    if missing:
        raise ValueError(
            f"Coordinate file is missing: {missing}"
        )

    print()
    print("Coordinate rows found:", len(towns))
    print(
        "Total missing features:",
        sum(len(v) for v in FEATURE_GROUPS.values())
    )

    for number, (group_name, variables) in enumerate(
        FEATURE_GROUPS.items(),
        start=1
    ):
        download_group(
            towns=towns,
            group_number=number,
            group_name=group_name,
            variables=variables
        )

    print()
    print("=" * 72)
    print("ALL API GROUPS FINISHED")
    print("=" * 72)

    print()
    print(
        "The two feature files remain separate intentionally."
    )
    print(
        "They can be merged later by "
        "prefecture + town + date."
    )


if __name__ == "__main__":
    main()
