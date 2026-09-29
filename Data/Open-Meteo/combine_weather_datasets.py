import os
import re
import glob
import csv
import pandas as pd

# ============================================================
# SETTINGS
# ============================================================

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))

WEATHER_FOLDER = os.path.join(SCRIPT_FOLDER, "Weather")
SOLAR_DEWPOINT_FOLDER = os.path.join(SCRIPT_FOLDER, "Daily_solar_dewpoint")
SURFACE_WIND_FOLDER = os.path.join(
    SCRIPT_FOLDER,
    "Daily_surface_pressure_wind_direction"
)
FLOOD_FOLDER = os.path.join(SCRIPT_FOLDER, "Flood")

MISSING_WEATHER_FILE = os.path.join(
    SCRIPT_FOLDER,
    "Missing_weather_dataset",
    "japan_missing_weather_2021_2026.csv"
)

OUTPUT_FOLDER = os.path.join(
    SCRIPT_FOLDER,
    "Combined_daily_dataset"
)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "japan_complete_daily_2021_2026.csv"
)

REPORT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "combine_report.txt"
)

START_DATE = "2021-01-01"
END_DATE = "2026-12-31"

# IMPORTANT:
# Hourly_cloud_humid_pressure is intentionally NOT read.
# Daily humidity/cloud values come from Missing_weather_dataset.

# Only flood columns required by the current Flood model.
FLOOD_KEEP = [
    "river_discharge",
    "river_discharge_p75",
    "river_discharge_mean",
    "river_discharge_median",
    "river_discharge_max",
]


# ============================================================
# COLUMN CLEANING
# ============================================================

def clean_column_name(name):
    """
    Convert Open-Meteo column headers such as:
        temperature_2m_max (°C)
    into:
        temperature_2m_max
    """
    name = str(name).strip()

    # Remove the final units section in parentheses.
    name = re.sub(r"\s*\([^)]*\)\s*$", "", name)

    name = name.strip()

    if name == "time":
        return "date"

    if name == "city/town":
        return "town"

    return name


def infer_prefecture_from_filename(path, dataset_type):
    """
    Existing group files are separated by prefecture.
    Remove each dataset's filename suffix to recover the
    prefecture/region name.
    """
    filename = os.path.splitext(os.path.basename(path))[0]

    suffixes = {
        "weather": "",
        "solar": "_solar_dewpoint",
        "surface": "_pressure_wind",
        "flood": "",
    }

    suffix = suffixes[dataset_type]

    if suffix and filename.endswith(suffix):
        filename = filename[:-len(suffix)]

    return filename


# ============================================================
# READ GROUP'S TWO-SECTION OPEN-METEO CSV FORMAT
# ============================================================

def read_two_section_csv(path, dataset_type):
    """
    The existing group files contain:

    location metadata
    blank line
    daily-data header
    daily data

    This function reads both sections and joins the location
    metadata onto every daily row.
    """

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    data_header_index = None

    for i, row in enumerate(rows):
        if (
            len(row) >= 2
            and row[0].strip() == "location_id"
            and row[1].strip() == "time"
        ):
            data_header_index = i
            break

    if data_header_index is None:
        raise ValueError(
            f"Could not find daily-data header in {path}"
        )

    # ---------------- LOCATION METADATA ----------------

    metadata_rows = rows[:data_header_index]

    # Remove blank rows.
    metadata_rows = [
        row for row in metadata_rows
        if any(str(value).strip() for value in row)
    ]

    if not metadata_rows:
        raise ValueError(
            f"No location metadata found in {path}"
        )

    metadata_header = [
        clean_column_name(x)
        for x in metadata_rows[0]
    ]

    metadata_data = metadata_rows[1:]

    metadata = pd.DataFrame(
        metadata_data,
        columns=metadata_header
    )

    # ---------------- DAILY DATA ----------------

    data_header = [
        clean_column_name(x)
        for x in rows[data_header_index]
    ]

    data_rows = [
        row
        for row in rows[data_header_index + 1:]
        if any(str(value).strip() for value in row)
    ]

    daily = pd.DataFrame(
        data_rows,
        columns=data_header
    )

    # ---------------- JOIN LOCATION INFO ----------------

    metadata["location_id"] = metadata["location_id"].astype(str)
    daily["location_id"] = daily["location_id"].astype(str)

    keep_metadata = [
        column
        for column in [
            "location_id",
            "town",
            "latitude",
            "longitude",
            "elevation",
        ]
        if column in metadata.columns
    ]

    daily = daily.merge(
        metadata[keep_metadata],
        on="location_id",
        how="left"
    )

    daily.insert(
        0,
        "prefecture",
        infer_prefecture_from_filename(
            path,
            dataset_type
        )
    )

    daily["date"] = pd.to_datetime(
        daily["date"],
        errors="coerce"
    )

    daily = daily[
        daily["date"].between(
            pd.Timestamp(START_DATE),
            pd.Timestamp(END_DATE)
        )
    ].copy()

    return daily


# ============================================================
# LOAD A WHOLE EXISTING DATASET FOLDER
# ============================================================

def load_folder(folder, dataset_type):
    if not os.path.isdir(folder):
        raise FileNotFoundError(
            f"Required folder not found:\n{folder}"
        )

    files = sorted(
        glob.glob(
            os.path.join(folder, "*.csv")
        )
    )

    if not files:
        raise FileNotFoundError(
            f"No CSV files found in:\n{folder}"
        )

    frames = []

    print(
        f"\nLoading {dataset_type}: "
        f"{len(files)} CSV files"
    )

    for number, path in enumerate(files, start=1):
        print(
            f"  [{number}/{len(files)}] "
            f"{os.path.basename(path)}"
        )

        frame = read_two_section_csv(
            path,
            dataset_type
        )

        frames.append(frame)

    result = pd.concat(
        frames,
        ignore_index=True
    )

    print(
        f"  -> {len(result):,} daily rows loaded"
    )

    return result


# ============================================================
# STANDARDIZE KEYS
# ============================================================

def normalize_keys(df):
    df = df.copy()

    df["prefecture"] = (
        df["prefecture"]
        .astype(str)
        .str.strip()
    )

    df["town"] = (
        df["town"]
        .astype(str)
        .str.strip()
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    return df


def check_duplicate_keys(df, name):
    keys = [
        "prefecture",
        "town",
        "date",
    ]

    duplicates = df.duplicated(
        keys,
        keep=False
    )

    count = int(duplicates.sum())

    if count > 0:
        print(
            f"WARNING: {name} has "
            f"{count:,} rows involved in duplicate keys."
        )

        # Keep first so duplicate rows do not multiply during merge.
        df = df.drop_duplicates(
            keys,
            keep="first"
        )

    return df


# ============================================================
# REMOVE DUPLICATE / UNNEEDED IDENTIFIER COLUMNS
# ============================================================

def select_dataset_columns(df, dataset_type):
    """
    Each source contributes only its own useful attributes.

    Location metadata comes from Weather, which acts as the
    base dataset.
    """

    keys = [
        "prefecture",
        "town",
        "date",
    ]

    if dataset_type == "weather":
        desired = [
            "location_id",
            "latitude",
            "longitude",
            "elevation",

            "temperature_2m_max",
            "temperature_2m_min",

            "wind_speed_10m_max",
            "wind_gusts_10m_max",

            "snowfall_sum",
            "rain_sum",
            "precipitation_hours",
            "precipitation_sum",
        ]

    elif dataset_type == "solar":
        desired = [
            "shortwave_radiation_sum",
            "sunshine_duration",
            "daylight_duration",
            "dew_point_2m_mean",
            "dew_point_2m_max",
        ]

    elif dataset_type == "surface":
        desired = [
            "wind_direction_10m_dominant",
            "surface_pressure_mean",
            "surface_pressure_max",
            "surface_pressure_min",
        ]

    elif dataset_type == "flood":
        desired = FLOOD_KEEP

    else:
        raise ValueError(
            f"Unknown dataset type: {dataset_type}"
        )

    existing = [
        column
        for column in desired
        if column in df.columns
    ]

    missing = [
        column
        for column in desired
        if column not in df.columns
    ]

    if missing:
        print(
            f"WARNING: {dataset_type} is missing "
            f"expected columns: {missing}"
        )

    return df[keys + existing].copy()


# ============================================================
# LOAD THE NEW 15-ATTRIBUTE DOWNLOAD
# ============================================================

def load_missing_weather():
    if not os.path.exists(MISSING_WEATHER_FILE):
        raise FileNotFoundError(
            "\nMissing-weather download is not finished/found.\n"
            f"Expected:\n{MISSING_WEATHER_FILE}\n\n"
            "Finish download_missing_weather.py first, "
            "then run this combination script."
        )

    print(
        "\nLoading Missing_weather_dataset..."
    )

    df = pd.read_csv(
        MISSING_WEATHER_FILE,
        low_memory=False
    )

    # Downloader already uses these names, but keep this robust.
    df = df.rename(
        columns={
            "Prefecture/Region": "prefecture",
            "Town": "town",
            "time": "date",
        }
    )

    required = [
        "prefecture",
        "town",
        "date",
    ]

    missing_required = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing_required:
        raise ValueError(
            "Missing-weather file does not contain "
            f"merge keys: {missing_required}"
        )

    df = normalize_keys(df)

    # These are the 15 fields intentionally downloaded.
    desired = [
        "temperature_2m_mean",

        "relative_humidity_2m_mean",
        "relative_humidity_2m_max",
        "relative_humidity_2m_min",

        "dew_point_2m_min",

        "cloud_cover_mean",
        "cloud_cover_max",
        "cloud_cover_min",

        "pressure_msl_mean",
        "pressure_msl_max",
        "pressure_msl_min",

        "wind_speed_10m_mean",
        "wind_speed_10m_min",

        "wind_gusts_10m_mean",
        "wind_gusts_10m_min",
    ]

    missing = [
        column
        for column in desired
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing-weather dataset is missing "
            f"expected attributes:\n{missing}"
        )

    df = df[
        [
            "prefecture",
            "town",
            "date",
        ]
        + desired
    ].copy()

    print(
        f"  -> {len(df):,} daily rows loaded"
    )

    return df


# ============================================================
# SAFE MERGE
# ============================================================

def merge_source(base, source, source_name):
    keys = [
        "prefecture",
        "town",
        "date",
    ]

    source = check_duplicate_keys(
        source,
        source_name
    )

    before = len(base)

    merged = base.merge(
        source,
        on=keys,
        how="left",
        validate="one_to_one"
    )

    if len(merged) != before:
        raise RuntimeError(
            f"{source_name} merge unexpectedly changed "
            f"row count from {before:,} to {len(merged):,}."
        )

    added_columns = [
        column
        for column in source.columns
        if column not in keys
    ]

    if added_columns:
        rows_with_any_match = (
            merged[added_columns]
            .notna()
            .any(axis=1)
            .sum()
        )
    else:
        rows_with_any_match = 0

    print(
        f"Merged {source_name}: "
        f"{rows_with_any_match:,}/{len(merged):,} "
        f"base rows matched"
    )

    return merged


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 76)
    print("COMBINE JAPAN DAILY DATASETS")
    print("=" * 76)

    print(
        "\nHourly_cloud_humid_pressure is intentionally ignored."
    )
    print(
        "Daily humidity/cloud attributes are taken directly "
        "from Missing_weather_dataset."
    )

    # --------------------------------------------------------
    # LOAD EXISTING RAW DAILY DATASETS
    # --------------------------------------------------------

    weather = load_folder(
        WEATHER_FOLDER,
        "weather"
    )

    solar = load_folder(
        SOLAR_DEWPOINT_FOLDER,
        "solar"
    )

    surface = load_folder(
        SURFACE_WIND_FOLDER,
        "surface"
    )

    flood = load_folder(
        FLOOD_FOLDER,
        "flood"
    )

    missing_weather = load_missing_weather()

    # --------------------------------------------------------
    # NORMALIZE MERGE KEYS
    # --------------------------------------------------------

    weather = normalize_keys(weather)
    solar = normalize_keys(solar)
    surface = normalize_keys(surface)
    flood = normalize_keys(flood)
    missing_weather = normalize_keys(missing_weather)

    # --------------------------------------------------------
    # KEEP ONLY REQUIRED COLUMNS
    # --------------------------------------------------------

    weather = select_dataset_columns(
        weather,
        "weather"
    )

    solar = select_dataset_columns(
        solar,
        "solar"
    )

    surface = select_dataset_columns(
        surface,
        "surface"
    )

    flood = select_dataset_columns(
        flood,
        "flood"
    )

    # --------------------------------------------------------
    # WEATHER IS THE BASE DAILY DATASET
    # --------------------------------------------------------

    weather = check_duplicate_keys(
        weather,
        "Weather"
    )

    combined = weather.copy()

    print(
        f"\nBase Weather rows: {len(combined):,}"
    )

    # --------------------------------------------------------
    # MERGE DAILY SOURCES
    # --------------------------------------------------------

    combined = merge_source(
        combined,
        solar,
        "Daily_solar_dewpoint"
    )

    combined = merge_source(
        combined,
        surface,
        "Daily_surface_pressure_wind_direction"
    )

    combined = merge_source(
        combined,
        missing_weather,
        "Missing_weather_dataset"
    )

    combined = merge_source(
        combined,
        flood,
        "Flood"
    )

    # --------------------------------------------------------
    # CALENDAR COLUMNS
    # --------------------------------------------------------

    combined["year"] = combined["date"].dt.year
    combined["month"] = combined["date"].dt.month
    combined["day"] = combined["date"].dt.day

    # Convert date back to clean YYYY-MM-DD text.
    combined["date"] = (
        combined["date"]
        .dt.strftime("%Y-%m-%d")
    )

    # --------------------------------------------------------
    # FINAL COLUMN ORDER
    # --------------------------------------------------------

    identifiers = [
        "location_id",
        "prefecture",
        "town",
        "latitude",
        "longitude",
        "elevation",
        "date",
        "year",
        "month",
        "day",
    ]

    identifiers = [
        column
        for column in identifiers
        if column in combined.columns
    ]

    remaining = [
        column
        for column in combined.columns
        if column not in identifiers
    ]

    combined = combined[
        identifiers + remaining
    ]

    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    key_columns = [
        "prefecture",
        "town",
        "date",
    ]

    duplicate_count = int(
        combined.duplicated(
            key_columns
        ).sum()
    )

    unique_towns = (
        combined[
            ["prefecture", "town"]
        ]
        .drop_duplicates()
        .shape[0]
    )

    weather_columns = [
        column
        for column in combined.columns
        if column not in identifiers
    ]

    missing_counts = (
        combined[weather_columns]
        .isna()
        .sum()
        .sort_values(ascending=False)
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print(
        "\nSaving combined dataset..."
    )

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report_lines = []

    report_lines.append(
        "JAPAN COMPLETE DAILY DATASET - COMBINATION REPORT"
    )
    report_lines.append(
        "=" * 60
    )
    report_lines.append(
        f"Output: {OUTPUT_FILE}"
    )
    report_lines.append(
        f"Date range requested: {START_DATE} to {END_DATE}"
    )
    report_lines.append(
        f"Rows: {len(combined):,}"
    )
    report_lines.append(
        f"Unique prefecture/town pairs: {unique_towns:,}"
    )
    report_lines.append(
        f"Duplicate prefecture+town+date rows: {duplicate_count:,}"
    )
    report_lines.append(
        f"Columns: {len(combined.columns)}"
    )

    report_lines.append("")
    report_lines.append(
        "NOTE: Hourly_cloud_humid_pressure was NOT used."
    )
    report_lines.append(
        "Daily humidity/cloud fields come directly from "
        "Missing_weather_dataset."
    )

    report_lines.append("")
    report_lines.append(
        "MISSING VALUES BY ATTRIBUTE"
    )
    report_lines.append(
        "-" * 60
    )

    for column, count in missing_counts.items():
        report_lines.append(
            f"{column}: {int(count):,}"
        )

    report_lines.append("")
    report_lines.append(
        "FINAL COLUMNS"
    )
    report_lines.append(
        "-" * 60
    )

    for column in combined.columns:
        report_lines.append(column)

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            "\n".join(report_lines)
        )

    # --------------------------------------------------------
    # DISPLAY SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 76)
    print("COMBINATION COMPLETE")
    print("=" * 76)

    print(
        f"Rows                 : {len(combined):,}"
    )
    print(
        f"Unique towns         : {unique_towns:,}"
    )
    print(
        f"Columns              : {len(combined.columns)}"
    )
    print(
        f"Duplicate daily keys : {duplicate_count:,}"
    )

    print("\nFinal dataset:")
    print(OUTPUT_FILE)

    print("\nValidation report:")
    print(REPORT_FILE)

    if unique_towns != 255:
        print(
            "\nWARNING: Final dataset does not contain exactly "
            "255 unique prefecture/town pairs."
        )

    if duplicate_count > 0:
        print(
            "\nWARNING: Duplicate daily rows were found. "
            "Check combine_report.txt."
        )

    print(
        "\nCheck combine_report.txt for missing values before "
        "using the dataset for model training."
    )


if __name__ == "__main__":
    main()
