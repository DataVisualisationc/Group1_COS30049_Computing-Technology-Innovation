import os
import pandas as pd
import geopandas as gpd
import fiona
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import nearest_points
from pyproj import Geod


# ============================================================
# SETTINGS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

INPUT_FILE = PROCESSED / "jma_day3_to_landfall_with_weather.csv"
SHAPE_FOLDER = ROOT / "data" / "gis" / "jp_shp"
OUTPUT_FILE = PROCESSED / "jma_day3_to_landfall_with_weather_prefecture.csv"

GEOD = Geod(ellps="WGS84")


# ============================================================
# PREFECTURE NAME FIXES
# ============================================================

NAME_FIXES = {
    "KÅchi": "Kōchi",
    "HokkaidÅ": "Hokkaidō",
    "ÅŒsaka": "Ōsaka",
    "KyÅto": "Kyōto",
    "ÅŒita": "Ōita",
}


def fix_name(name):

    if pd.isna(name):
        return name

    return NAME_FIXES.get(name, name)


# ============================================================
# GEODESIC DISTANCE
# ============================================================

def distance_km(lon1, lat1, lon2, lat2):

    _, _, distance_m = GEOD.inv(
        lon1,
        lat1,
        lon2,
        lat2
    )

    return distance_m / 1000.0


# ============================================================
# DISTANCE FROM POINT TO PREFECTURE
# ============================================================

def distance_to_prefecture(point, geometry):

    # Storm is inside prefecture
    if geometry.contains(point) or geometry.touches(point):

        return 0.0

    # Find closest point on prefecture polygon
    closest_point = nearest_points(
        point,
        geometry
    )[1]

    return distance_km(
        point.x,
        point.y,
        closest_point.x,
        closest_point.y
    )


# ============================================================
# FIND 47-PREFECTURE GIS LAYER
# ============================================================

def find_prefecture_layer():

    print("\nSearching for 47-prefecture layer...")

    if not os.path.exists(SHAPE_FOLDER):

        raise FileNotFoundError(
            f"Cannot find folder: {SHAPE_FOLDER}"
        )

    gis_files = []

    # Search jp_shp and all subfolders
    for root, dirs, files in os.walk(SHAPE_FOLDER):

        for filename in files:

            if filename.lower().endswith(
                (
                    ".shp",
                    ".gpkg",
                    ".geojson",
                    ".json"
                )
            ):

                path = os.path.join(
                    root,
                    filename
                )

                gis_files.append(path)

    print("GIS files found:", len(gis_files))

    if len(gis_files) == 0:

        raise FileNotFoundError(
            "No GIS files found inside jp_shp."
        )

    # --------------------------------------------------------
    # Search files/layers
    # --------------------------------------------------------

    for file_path in gis_files:

        print("\nChecking:", file_path)

        try:

            layers = fiona.listlayers(file_path)

        except Exception:

            layers = []

        # ----------------------------------------------------
        # Check layers
        # ----------------------------------------------------

        for layer in layers:

            try:

                gdf = gpd.read_file(
                    file_path,
                    layer=layer
                )

            except Exception:

                continue

            print(
                "   Layer:",
                layer,
                "| rows:",
                len(gdf)
            )

            # Your correct prefecture layer
            # previously had 47 rows + "name"
            if (
                len(gdf) == 47
                and "name" in gdf.columns
            ):

                print("\nFOUND PREFECTURE LAYER!")

                print("File :", file_path)
                print("Layer:", layer)

                return gdf

        # ----------------------------------------------------
        # Try default layer
        # ----------------------------------------------------

        try:

            gdf = gpd.read_file(file_path)

        except Exception:

            continue

        if (
            len(gdf) == 47
            and "name" in gdf.columns
        ):

            print("\nFOUND PREFECTURE LAYER!")

            print("File:", file_path)

            return gdf

    raise ValueError(
        "Could not find a GIS layer "
        "containing 47 prefectures."
    )


# ============================================================
# FIND NEAREST PREFECTURE FOR ONE STORM POINT
# ============================================================

def find_nearest(
    latitude,
    longitude,
    prefectures
):

    point = Point(
        longitude,
        latitude
    )

    nearest_name = None
    nearest_distance = float("inf")

    for _, prefecture in prefectures.iterrows():

        geometry = prefecture["geometry"]

        dist = distance_to_prefecture(
            point,
            geometry
        )

        if dist < nearest_distance:

            nearest_distance = dist

            nearest_name = prefecture["name"]

    return (
        fix_name(nearest_name),
        nearest_distance
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ADD NEAREST PREFECTURE")
    print("=" * 60)

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    print("\nLoading:", INPUT_FILE)

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"\nCannot find {INPUT_FILE}\n"
            "Put it in the same folder as this script."
        )

    df = pd.read_csv(INPUT_FILE)

    print("Rows loaded:", len(df))

    print("\nColumns:")
    print(df.columns.tolist())

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    if "latitude" not in df.columns:

        raise ValueError(
            "CSV does not contain latitude."
        )

    if "longitude" not in df.columns:

        raise ValueError(
            "CSV does not contain longitude."
        )

    # --------------------------------------------------------
    # Load prefectures
    # --------------------------------------------------------

    prefectures = find_prefecture_layer()

    print(
        "\nPrefectures loaded:",
        len(prefectures)
    )

    print(
        "CRS:",
        prefectures.crs
    )

    if prefectures.crs is None:

        raise ValueError(
            "Prefecture GIS file has no CRS."
        )

    # Convert to normal latitude/longitude
    prefectures = prefectures.to_crs(
        "EPSG:4326"
    )

    # --------------------------------------------------------
    # Fix names BEFORE matching
    # --------------------------------------------------------

    prefectures["name"] = (
        prefectures["name"]
        .apply(fix_name)
    )

    print("\nPrefecture names:")

    for name in sorted(
        prefectures["name"]
        .dropna()
        .unique()
    ):

        print(" ", name)

    # --------------------------------------------------------
    # Find nearest prefecture
    # --------------------------------------------------------

    print(
        "\nFinding nearest prefecture "
        "for all rows..."
    )

    nearest_names = []
    nearest_distances = []

    total = len(df)

    for i, row in df.iterrows():

        lat = float(
            row["latitude"]
        )

        lon = float(
            row["longitude"]
        )

        # JMA may occasionally use 0-360 longitude
        if lon > 180:

            lon = (
                (lon + 180) % 360
            ) - 180

        name, dist = find_nearest(
            latitude=lat,
            longitude=lon,
            prefectures=prefectures
        )

        nearest_names.append(name)

        nearest_distances.append(
            round(dist, 3)
        )

        # Progress
        if (
            (i + 1) % 25 == 0
            or (i + 1) == total
        ):

            print(
                f"{i + 1}/{total}"
            )

    # ========================================================
    # NOW CREATE THE COLUMNS
    #
    # Notice:
    # We only access nearest_prefecture AFTER creating it.
    # This fixes your KeyError.
    # ========================================================

    df["nearest_prefecture"] = (
        nearest_names
    )

    df["distance_to_prefecture_km"] = (
        nearest_distances
    )

    # --------------------------------------------------------
    # Final name cleanup
    # --------------------------------------------------------

    df["nearest_prefecture"] = (
        df["nearest_prefecture"]
        .apply(fix_name)
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        "\nTotal rows:",
        len(df)
    )

    print(
        "Rows with prefecture:",
        df["nearest_prefecture"]
        .notna()
        .sum()
    )

    print(
        "Missing:",
        df["nearest_prefecture"]
        .isna()
        .sum()
    )

    print(
        "Unique nearest prefectures:",
        df["nearest_prefecture"]
        .nunique()
    )

    print(
        "\nPrefecture counts:"
    )

    print(
        df["nearest_prefecture"]
        .value_counts()
    )

    # --------------------------------------------------------
    # Encoding check
    # --------------------------------------------------------

    broken = df[
        df["nearest_prefecture"]
        .astype(str)
        .str.contains(
            "Å",
            na=False
        )
    ]

    print(
        "\nSuspicious encoding rows:",
        len(broken)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)
    print("FINISHED")
    print("=" * 60)

    print(
        "\nSaved:",
        OUTPUT_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()