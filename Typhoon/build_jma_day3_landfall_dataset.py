import argparse
import pandas as pd
import numpy as np

# ============================================================
# JMA DAILY LANDFALL-CENTERED DATASET
#
# For every true JMA "#" landfall event:
#   Day -3 -> Low
#   Day -2 -> Moderate
#   Day -1 -> High
#   Day  0 -> High (actual landfall)
#
# One row per storm/event/calendar day.
# No 70-km filter is used for Day -3/-2/-1.
# ============================================================


def parse_time_token(token):
    token = str(token).zfill(8)
    yy = int(token[0:2])
    mm = int(token[2:4])
    dd = int(token[4:6])
    hh = int(token[6:8])
    year = 1900 + yy if yy >= 51 else 2000 + yy
    return year, mm, dd, hh


def parse_bst(path):
    rows = []
    storm = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue

            if line.startswith("66666"):
                padded = line.ljust(80)
                intl_id = padded[6:10].strip()
                storm_number = padded[16:20].strip()
                storm_name = padded[30:50].strip()
                last_revision_date = padded[64:72].strip()

                if not intl_id.isdigit():
                    storm = None
                    continue

                storm = {
                    "intl_id": intl_id,
                    "storm_number": storm_number,
                    "storm_name": storm_name if storm_name else "UNNAMED",
                    "last_revision_date": last_revision_date,
                }
                continue

            if storm is None:
                continue

            tokens = line.split()
            if len(tokens) < 6:
                continue

            try:
                year, month, day, hour = parse_time_token(tokens[0])
                lat = float(tokens[3]) / 10.0
                lon = float(tokens[4]) / 10.0

                # Normalize longitude to [-180, 180)
                lon = ((lon + 180.0) % 360.0) - 180.0

                row = {
                    **storm,
                    "datetime_yymmddhh": str(tokens[0]).zfill(8),
                    "datetime": pd.Timestamp(year, month, day, hour),
                    "date": pd.Timestamp(year, month, day),
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "indicator": tokens[1],
                    "grade": pd.to_numeric(tokens[2], errors="coerce"),
                    "latitude": lat,
                    "longitude": lon,
                    "pressure_hpa": pd.to_numeric(tokens[5], errors="coerce"),
                    "wind_speed_kt": (
                        pd.to_numeric(tokens[6], errors="coerce")
                        if len(tokens) >= 7 else np.nan
                    ),
                    "dir_r50": None,
                    "r50_long_nm": np.nan,
                    "r50_short_nm": np.nan,
                    "dir_r30": None,
                    "r30_long_nm": np.nan,
                    "r30_short_nm": np.nan,
                    "landfall": "landfall" if "#" in line else "",
                }

                # Preserve radius fields when present.
                if len(tokens) >= 11:
                    r50 = tokens[7]
                    r30 = tokens[9]

                    if len(r50) >= 2:
                        row["dir_r50"] = r50[0]
                        row["r50_long_nm"] = pd.to_numeric(
                            r50[1:], errors="coerce"
                        )
                    row["r50_short_nm"] = pd.to_numeric(
                        tokens[8], errors="coerce"
                    )

                    if len(r30) >= 2:
                        row["dir_r30"] = r30[0]
                        row["r30_long_nm"] = pd.to_numeric(
                            r30[1:], errors="coerce"
                        )
                    row["r30_short_nm"] = pd.to_numeric(
                        tokens[10], errors="coerce"
                    )

                rows.append(row)

            except (ValueError, IndexError):
                continue

    return pd.DataFrame(rows)


def risk_from_day(days_before):
    if days_before == 3:
        return "Low"
    if days_before == 2:
        return "Moderate"
    return "High"  # Day -1 and Day 0


def choose_day_row(day_rows, landfall_datetime, days_before):
    """
    Select one JMA observation for the requested calendar day.

    Day 0:
      preserve the actual # landfall observation.

    Day -1/-2/-3:
      choose the LAST JMA observation on that calendar day.
      This represents the latest known storm state before the next day.
    """
    if days_before == 0:
        lf = day_rows[day_rows["landfall"].eq("landfall")].copy()

        if not lf.empty:
            # Choose the landfall observation corresponding most closely
            # to this event time if multiple '#' rows exist that day.
            lf["time_difference"] = (
                lf["datetime"] - landfall_datetime
            ).abs()

            return (
                lf.sort_values(["time_difference", "datetime"])
                .drop(columns=["time_difference"])
                .iloc[0]
            )

    return day_rows.sort_values("datetime").iloc[-1]


def build_sequences(df):
    landfalls = (
        df[df["landfall"].eq("landfall")]
        .sort_values(["intl_id", "datetime"])
        .copy()
    )

    print(f"True JMA landfall observations found: {len(landfalls)}")

    output_rows = []
    event_counter = 0

    for lf in landfalls.itertuples(index=False):
        event_counter += 1

        event_id = (
            f"{lf.intl_id}_"
            f"{lf.datetime.strftime('%Y%m%d%H')}"
        )

        storm_rows = df[df["intl_id"].eq(lf.intl_id)].copy()

        landfall_date = pd.Timestamp(lf.date)

        for days_before in [3, 2, 1, 0]:
            target_date = (
                landfall_date
                - pd.Timedelta(days=days_before)
            )

            day_rows = storm_rows[
                storm_rows["date"].eq(target_date)
            ].copy()

            if day_rows.empty:
                # Keep missing-day information for diagnostics,
                # but do not create a fake meteorological row.
                continue

            selected = choose_day_row(
                day_rows,
                pd.Timestamp(lf.datetime),
                days_before
            ).copy()

            selected["landfall_event_id"] = event_id
            selected["landfall_datetime"] = pd.Timestamp(lf.datetime)
            selected["landfall_date"] = landfall_date
            selected["days_before_landfall"] = days_before
            selected["relative_day"] = (
                "Day 0"
                if days_before == 0
                else f"Day -{days_before}"
            )
            selected["risk"] = risk_from_day(days_before)

            # Only the event's actual Day-0 selected row should be
            # marked as the target landfall row in the final sequence.
            selected["is_landfall_day"] = days_before == 0

            output_rows.append(selected)

    if not output_rows:
        return pd.DataFrame()

    result = pd.DataFrame(output_rows)

    # If two # observations are so close that they create duplicate
    # event/day combinations, retain one deterministically.
    result = (
        result
        .sort_values(
            ["landfall_event_id", "days_before_landfall", "datetime"]
        )
        .drop_duplicates(
            ["landfall_event_id", "days_before_landfall"],
            keep="last"
        )
        .reset_index(drop=True)
    )

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bst",
        default="bst_all.txt",
        help="Raw JMA bst_all.txt"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2000
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2026
    )
    parser.add_argument(
        "--output",
        default="jma_day3_to_landfall_before_weather.csv"
    )

    args = parser.parse_args()

    print("\nSTEP 1 - Parsing raw JMA bst_all.txt")
    df = parse_bst(args.bst)

    # Keep enough prior records for landfalls in the selected period.
    selected_landfall_period = df[
        df["year"].between(args.start_year, args.end_year)
        & df["landfall"].eq("landfall")
    ].copy()

    valid_storm_ids = selected_landfall_period["intl_id"].unique()

    # Keep full tracks for selected storms so Day -3 is not lost
    # around the start-year boundary.
    df = df[df["intl_id"].isin(valid_storm_ids)].copy()

    print(
        f"Landfall period: {args.start_year}-{args.end_year}"
    )
    print(
        f"Storms with landfall records: {len(valid_storm_ids)}"
    )
    print(
        f"Landfall events in period: {len(selected_landfall_period)}"
    )

    # Build only from landfalls in requested period.
    # Temporarily mark out-of-period landfall rows so they cannot
    # become sequence anchors.
    df["_original_landfall"] = df["landfall"]
    in_period = df["year"].between(
        args.start_year,
        args.end_year
    )
    df.loc[~in_period, "landfall"] = ""

    print("\nSTEP 2 - Building Day -3 to Day 0 sequences")
    result = build_sequences(df)

    if result.empty:
        raise ValueError("No landfall-centered sequences were produced.")

    result = result.drop(
        columns=["_original_landfall"],
        errors="ignore"
    )

    # --------------------------------------------------------
    # Sequence diagnostics
    # --------------------------------------------------------
    counts = (
        result.groupby("landfall_event_id")[
            "days_before_landfall"
        ]
        .nunique()
    )

    complete_event_ids = counts[counts == 4].index

    result["complete_4day_sequence"] = (
        result["landfall_event_id"]
        .isin(complete_event_ids)
    )

    print("\nSTEP 3 - Dataset validation")

    print(f"Rows produced: {len(result)}")
    print(
        "Landfall events represented:",
        result["landfall_event_id"].nunique()
    )
    print(
        "Complete Day -3/-2/-1/0 sequences:",
        len(complete_event_ids)
    )
    print(
        "Incomplete sequences:",
        (counts < 4).sum()
    )

    print("\nRows by relative day:")
    print(
        result["relative_day"]
        .value_counts()
        .reindex(["Day -3", "Day -2", "Day -1", "Day 0"])
        .fillna(0)
        .astype(int)
    )

    print("\nRisk distribution:")
    print(
        result["risk"]
        .value_counts()
        .reindex(["Low", "Moderate", "High"])
        .fillna(0)
        .astype(int)
    )

    print("\nComplete-sequence-only risk distribution:")
    complete = result[result["complete_4day_sequence"]]

    print(
        complete["risk"]
        .value_counts()
        .reindex(["Low", "Moderate", "High"])
        .fillna(0)
        .astype(int)
    )

    # Useful column order for later Open-Meteo merge.
    first = [
        "landfall_event_id",
        "intl_id",
        "storm_number",
        "storm_name",
        "date",
        "datetime",
        "days_before_landfall",
        "relative_day",
        "risk",
        "complete_4day_sequence",
        "is_landfall_day",
        "landfall_datetime",
        "landfall_date",
        "latitude",
        "longitude",
        "grade",
        "pressure_hpa",
        "wind_speed_kt",
        "dir_r50",
        "r50_long_nm",
        "r50_short_nm",
        "dir_r30",
        "r30_long_nm",
        "r30_short_nm",
    ]

    rest = [c for c in result.columns if c not in first]
    result = result[first + rest]

    result = result.sort_values(
        ["landfall_datetime", "days_before_landfall"],
        ascending=[True, False]
    ).reset_index(drop=True)

    result.to_csv(args.output, index=False)

    print("\n" + "=" * 65)
    print("FINISHED")
    print("=" * 65)
    print(f"Output: {args.output}")
    print(
        "\nNo Open-Meteo data has been downloaded yet."
    )
    print(
        "Inspect complete_4day_sequence before the weather step."
    )


if __name__ == "__main__":
    main()
