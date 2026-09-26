import pandas as pd
import requests
import time
from datetime import timedelta


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "landfall_2000_2025.csv"
OUTPUT_FILE = "typhoon_data_with_weather.csv"

DAYS_BEFORE = 7

API_URL = "https://archive-api.open-meteo.com/v1/archive"


# ============================================================
# OPEN-METEO DAILY WEATHER VARIABLES
# ============================================================

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "cloud_cover_mean",
    "surface_pressure_mean",
    "surface_pressure_max",
    "surface_pressure_min",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum"
]


# ============================================================
# READ STORM DATA
# ============================================================

print("Reading typhoon dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Total typhoon observations: {len(df)}")


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "intl_id",
    "storm_number",
    "storm_name",
    "last_revision_date",
    "datetime",
    "year",
    "month",
    "day",
    "hour",
    "indicator",
    "grade",
    "latitude",
    "longitude",
    "pressure",
    "wind_speed",
    "dir_r50",
    "r50_long",
    "r50_short",
    "dir_r30",
    "r30_long",
    "r30_short",
    "landfall"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    print(missing_columns)

    raise ValueError(
        "Your CSV does not contain all required columns."
    )


# ============================================================
# CREATE CORRECT DATETIME
# ============================================================


df["storm_datetime"] = pd.to_datetime(
    {
        "year": df["year"],
        "month": df["month"],
        "day": df["day"],
        "hour": df["hour"]
    },
    errors="coerce"
)


# Check whether any dates failed

invalid_dates = df["storm_datetime"].isna().sum()

if invalid_dates > 0:
    print(
        f"WARNING: {invalid_dates} rows have invalid dates."
    )


# ============================================================
# FUNCTION TO GET WEATHER
# ============================================================

def get_weather(latitude, longitude, start_date, end_date):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),

        "daily": ",".join(DAILY_VARIABLES),

        "timezone": "auto",

        "cell_selection": "nearest"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    # Show Open-Meteo's error message if request fails
    if response.status_code != 200:

        print("\nOpen-Meteo response:")
        print(response.text)

        response.raise_for_status()

    return response.json()


# ============================================================
# CACHE
# ============================================================


weather_cache = {}


# ============================================================
# OUTPUT ROWS
# ============================================================

output_rows = []

total_rows = len(df)


# ============================================================
# PROCESS EACH STORM OBSERVATION
# ============================================================

for index, row in df.iterrows():

    print()
    print("=" * 70)
    print(f"Processing {index + 1}/{total_rows}")

    # --------------------------------------------------------
    # COPY ORIGINAL ROW
    # --------------------------------------------------------

    output_row = row.to_dict()


    # --------------------------------------------------------
    # GET STORM INFORMATION
    # --------------------------------------------------------

    storm_datetime = row["storm_datetime"]

    storm_name = row["storm_name"]


    # --------------------------------------------------------
    # FIX COORDINATES
    # --------------------------------------------------------
    #
    # Your dataset stores coordinates ×10.
    #
    # Example:
    #
    # 265  -> 26.5
    # 1280 -> 128.0
    #
    # --------------------------------------------------------

    latitude = row["latitude"] / 10
    longitude = row["longitude"] / 10


    # --------------------------------------------------------
    # VALIDATE DATETIME
    # --------------------------------------------------------

    if pd.isna(storm_datetime):

        print("Skipping row because datetime is invalid.")

        output_rows.append(output_row)

        continue


    # --------------------------------------------------------
    # VALIDATE COORDINATES
    # --------------------------------------------------------

    if pd.isna(latitude) or pd.isna(longitude):

        print("Skipping row because coordinates are missing.")

        output_rows.append(output_row)

        continue


    # Latitude must be between -90 and 90

    if latitude < -90 or latitude > 90:

        print(
            f"Skipping row: invalid latitude {latitude}"
        )

        output_rows.append(output_row)

        continue


    # Longitude must be between -180 and 180

    if longitude < -180 or longitude > 180:

        print(
            f"Skipping row: invalid longitude {longitude}"
        )

        output_rows.append(output_row)

        continue


    # --------------------------------------------------------
    # STORM DATE
    # --------------------------------------------------------

    storm_date = storm_datetime.normalize()


    # --------------------------------------------------------
    # CALCULATE PREVIOUS 7 DAYS
    # --------------------------------------------------------
    

    start_date = (
        storm_date -
        timedelta(days=DAYS_BEFORE)
    )

    end_date = (
        storm_date -
        timedelta(days=1)
    )


    # --------------------------------------------------------
    # SHOW WHAT WE ARE PROCESSING
    # --------------------------------------------------------

    print(f"Storm: {storm_name}")

    print(
        f"Storm datetime: {storm_datetime}"
    )

    print(
        f"Original coordinates: "
        f"{row['latitude']}, {row['longitude']}"
    )

    print(
        f"Converted coordinates: "
        f"{latitude}, {longitude}"
    )

    print(
        f"Getting weather from "
        f"{start_date.date()} "
        f"to "
        f"{end_date.date()}"
    )


    # --------------------------------------------------------
    # CACHE KEY
    # --------------------------------------------------------

    cache_key = (
        float(latitude),
        float(longitude),
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


    try:

        # ====================================================
        # CHECK CACHE
        # ====================================================

        if cache_key in weather_cache:

            print("Using cached weather data.")

            weather = weather_cache[
                cache_key
            ]


        # ====================================================
        # REQUEST OPEN-METEO
        # ====================================================

        else:

            print("Requesting Open-Meteo...")

            weather = get_weather(
                latitude,
                longitude,
                start_date,
                end_date
            )

            weather_cache[
                cache_key
            ] = weather

            # Avoid sending requests too quickly
            time.sleep(0.5)


        # ====================================================
        # GET DAILY DATA
        # ====================================================

        daily = weather.get("daily")


        if daily is None:

            raise ValueError(
                "Open-Meteo returned no daily weather data."
            )


        # ====================================================
        # CREATE DATE LOOKUP
        # ====================================================

        weather_dates = daily["time"]

        date_lookup = {}


        for i, weather_date in enumerate(
            weather_dates
        ):

            date_lookup[
                weather_date
            ] = {}

            for variable in DAILY_VARIABLES:

                date_lookup[
                    weather_date
                ][variable] = (
                    daily[variable][i]
                )


        # ====================================================
        # ADD PREVIOUS 7 DAYS TO ROW
        # ====================================================

        for days_before in range(
            7,
            0,
            -1
        ):

            target_date = (
                storm_date -
                timedelta(
                    days=days_before
                )
            )


            target_date_string = (
                target_date.strftime(
                    "%Y-%m-%d"
                )
            )


            # ------------------------------------------------
            # SAVE WEATHER DATE
            # ------------------------------------------------

            output_row[
                f"weather_date_day_{days_before}"
            ] = target_date_string


            # ------------------------------------------------
            # GET WEATHER FOR THAT DATE
            # ------------------------------------------------

            weather_for_day = (
                date_lookup.get(
                    target_date_string
                )
            )


            # ------------------------------------------------
            # WEATHER FOUND
            # ------------------------------------------------

            if weather_for_day:

                for variable in DAILY_VARIABLES:

                    output_row[
                        f"{variable}_day_{days_before}"
                    ] = (
                        weather_for_day.get(
                            variable
                        )
                    )


            # ------------------------------------------------
            # WEATHER MISSING
            # ------------------------------------------------

            else:

                print(
                    f"WARNING: "
                    f"No weather found for "
                    f"{target_date_string}"
                )

                for variable in DAILY_VARIABLES:

                    output_row[
                        f"{variable}_day_{days_before}"
                    ] = None


        # ====================================================
        # SAVE API INFORMATION
        # ====================================================

        output_row[
            "weather_api_latitude"
        ] = weather.get(
            "latitude"
        )

        output_row[
            "weather_api_longitude"
        ] = weather.get(
            "longitude"
        )

        output_row[
            "weather_api_elevation"
        ] = weather.get(
            "elevation"
        )

        output_row[
            "weather_api_timezone"
        ] = weather.get(
            "timezone"
        )


        print(
            "Weather added successfully!"
        )


    # ========================================================
    # REQUEST ERROR
    # ========================================================

    except requests.exceptions.RequestException as error:

        print()
        print("API ERROR:")
        print(error)


    # ========================================================
    # OTHER ERROR
    # ========================================================

    except Exception as error:

        print()
        print("ERROR:")
        print(error)


    # --------------------------------------------------------
    # ADD ROW TO FINAL DATA
    # --------------------------------------------------------

    output_rows.append(
        output_row
    )


# ============================================================
# CREATE FINAL DATAFRAME
# ============================================================

print()
print("=" * 70)
print("Creating final dataset...")

final_df = pd.DataFrame(
    output_rows
)


# ============================================================
# REMOVE TEMPORARY DATETIME
# ============================================================


if "storm_datetime" in final_df.columns:

    final_df.drop(
        columns=["storm_datetime"],
        inplace=True
    )


# ============================================================
# SAVE CSV
# ============================================================

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 70)
print("FINISHED")
print("=" * 70)

print(
    f"Original storm rows: "
    f"{len(df)}"
)

print(
    f"Final rows: "
    f"{len(final_df)}"
)

print(
    f"Unique Open-Meteo requests: "
    f"{len(weather_cache)}"
)

print(
    f"Output saved as: "
    f"{OUTPUT_FILE}"
)