from pathlib import Path
from io import StringIO
import pandas as pd
import numpy as np
import re

ROOT = Path(__file__).resolve().parent
OPEN_METEO = ROOT.parent / "Data" / "Open-Meteo"
OUT = ROOT / "dataset" / "flood_preprocessed.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Reference thresholds derived from the known flood samples.
# These are project-defined, NOT official JMA/Open-Meteo thresholds.
TH = {
    "rain_sum_past_3day": 46.30,
    "rain_sum_past_7day": 71.40,
    "max_daily_rain_past_7day": 36.80,
    "precipitation_hours_past_7day": 58.0,
    "river_discharge_previous_day": 9.47,
    "river_discharge_mean_7day": 2.64,
    "river_discharge_max_7day": 9.47,
    "discharge_ratio": 3.14,
}

def clean_columns(df):
    df.columns = [re.sub(r"\s*\([^)]*\)\s*$", "", str(c).strip()) for c in df.columns]
    return df.rename(columns={"time":"date", "city/town":"town"})

def read_openmeteo_csv(path):
    """Read ordinary CSVs and the project's metadata + blank-line + daily-table format."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    parts = re.split(r"\r?\n\s*\r?\n", text, maxsplit=1)
    if len(parts) == 2:
        try:
            meta = clean_columns(pd.read_csv(StringIO(parts[0])))
            daily = clean_columns(pd.read_csv(StringIO(parts[1])))
            if "location_id" in meta.columns and "location_id" in daily.columns:
                keep = [c for c in ["location_id","town","latitude","longitude","elevation"] if c in meta.columns]
                daily = daily.merge(meta[keep].drop_duplicates("location_id"),
                                    on="location_id", how="left", suffixes=("","_meta"))
            return daily
        except Exception:
            pass
    return clean_columns(pd.read_csv(path))

def normalize(df):
    aliases = {
        "rain_sum_day":"rain_sum",
        "precipitation_sum_day":"precipitation_sum",
        "precipitation_hours_day":"precipitation_hours",
        "river_discharge_day":"river_discharge",
    }
    return df.rename(columns={k:v for k,v in aliases.items() if k in df.columns})

def infer_prefecture(path):
    # Prefer parent folder only as a fallback identifier.
    name = path.stem
    for suffix in ["_pressure_wind", "_solar_dewpoint", "_river_discharge",
                   "_flood", "_weather", "_daily"]:
        name = name.replace(suffix, "")
    return name

print("="*72)
print("FLOOD PREPROCESSING - INDIVIDUAL FILES -> CONCATENATED DATASET")
print("="*72)
print("Searching:", OPEN_METEO)

if not OPEN_METEO.exists():
    raise FileNotFoundError(f"Open-Meteo folder not found: {OPEN_METEO}")

weather_parts, discharge_parts = [], []

for path in OPEN_METEO.rglob("*.csv"):
    try:
        d = normalize(read_openmeteo_csv(path))
    except Exception:
        continue

    cols = set(d.columns)

    # We need daily rain. precipitation_hours is preferred; if absent,
    # it is left unavailable rather than fabricated.
    if "date" in cols and "rain_sum" in cols:
        x = d.copy()
        if "prefecture" not in x.columns:
            x["prefecture"] = infer_prefecture(path)
        weather_parts.append(x)

    if "date" in cols and "river_discharge" in cols:
        x = d.copy()
        if "prefecture" not in x.columns:
            x["prefecture"] = infer_prefecture(path)
        discharge_parts.append(x)

if not weather_parts:
    raise FileNotFoundError("No individual CSV containing date/time + rain_sum was found under Data/Open-Meteo.")
if not discharge_parts:
    raise FileNotFoundError("No individual CSV containing date/time + river_discharge was found under Data/Open-Meteo.")

weather = pd.concat(weather_parts, ignore_index=True, sort=False)
river = pd.concat(discharge_parts, ignore_index=True, sort=False)

for d in (weather, river):
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    if "location_id" in d.columns:
        d["location_id"] = pd.to_numeric(d["location_id"], errors="coerce")

# Determine merge keys. Prefecture is included because location_id can restart in each file.
keys = ["prefecture", "date"]
if "location_id" in weather.columns and "location_id" in river.columns:
    keys.insert(1, "location_id")
elif "town" in weather.columns and "town" in river.columns:
    keys.insert(1, "town")
else:
    raise KeyError("Weather and river datasets need a shared location_id or town column.")

wcols = keys + [c for c in ["town","rain_sum","precipitation_hours","elevation"] if c in weather.columns and c not in keys]
rcols = keys + ["river_discharge"]

weather = weather[wcols].drop_duplicates(keys)
river = river[rcols].drop_duplicates(keys)

df = weather.merge(river, on=keys, how="inner")

for c in ["rain_sum","precipitation_hours","river_discharge","elevation"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

if "precipitation_hours" not in df.columns:
    print("\nWARNING: precipitation_hours was not found.")
    print("The precipitation-hours condition will be unavailable and will score 0.")
    df["precipitation_hours"] = np.nan

group_cols = ["prefecture"] + (["location_id"] if "location_id" in df.columns else ["town"])
df = df.dropna(subset=["date","rain_sum","river_discharge"]).sort_values(group_cols+["date"])

def add_history(g):
    g = g.sort_values("date").copy()
    rain = g["rain_sum"].shift(1)
    ph = g["precipitation_hours"].shift(1)
    q = g["river_discharge"].shift(1)

    g["rain_sum_past_3day"] = rain.rolling(3, min_periods=3).sum()
    g["rain_sum_past_7day"] = rain.rolling(7, min_periods=7).sum()
    g["max_daily_rain_past_7day"] = rain.rolling(7, min_periods=7).max()
    g["rain_flag_50mm"] = (rain.rolling(7, min_periods=7).max() > 50).astype("Int64")
    g["precipitation_hours_past_7day"] = ph.rolling(7, min_periods=7).sum()

    g["river_discharge_previous_day"] = q
    g["river_discharge_mean_7day"] = q.rolling(7, min_periods=7).mean()
    g["river_discharge_median_7day"] = q.rolling(7, min_periods=7).median()
    g["river_discharge_max_7day"] = q.rolling(7, min_periods=7).max()
    g["discharge_ratio"] = q / g["river_discharge"].shift(5).replace(0, np.nan)
    return g

df = df.groupby(group_cols, group_keys=False, dropna=False).apply(add_history).reset_index(drop=True)

# Threshold flags
pairs = {
    "cond_rain_3day":"rain_sum_past_3day",
    "cond_rain_7day":"rain_sum_past_7day",
    "cond_max_daily_rain":"max_daily_rain_past_7day",
    "cond_precipitation_hours":"precipitation_hours_past_7day",
    "cond_discharge_absolute":"river_discharge_previous_day",
    "cond_discharge_mean":"river_discharge_mean_7day",
    "cond_discharge_max":"river_discharge_max_7day",
    "cond_discharge_ratio":"discharge_ratio",
}
for flag, col in pairs.items():
    df[flag] = (df[col] >= TH[col]).fillna(False).astype(int)

rain_flags = ["cond_rain_3day","cond_rain_7day","cond_max_daily_rain","cond_precipitation_hours"]
river_flags = ["cond_discharge_absolute","cond_discharge_mean","cond_discharge_max","cond_discharge_ratio"]

df["rain_condition_score"] = df[rain_flags].sum(axis=1)
df["river_condition_score"] = df[river_flags].sum(axis=1)
df["flood_condition_score"] = df["rain_condition_score"] + df["river_condition_score"]

# Project-defined risk labels.
high = (df["rain_condition_score"] >= 3) & (df["river_condition_score"] >= 2)
medium = (
    ((df["rain_condition_score"] >= 2) & (df["river_condition_score"] >= 1))
    | (df["flood_condition_score"] >= 4)
)
df["flood_class"] = np.select([high, medium], ["High","Medium"], default="Low")

needed_history = [
    "rain_sum_past_3day","rain_sum_past_7day","max_daily_rain_past_7day",
    "river_discharge_previous_day","river_discharge_mean_7day",
    "river_discharge_median_7day","river_discharge_max_7day","discharge_ratio"
]
df = df.dropna(subset=needed_history).copy()
df["month"] = df["date"].dt.month

df.to_csv(OUT, index=False)

print("\nWeather rows found :", len(weather))
print("Discharge rows found:", len(river))
print("Merged/final rows   :", len(df))
print("Date range          :", df["date"].min(), "to", df["date"].max())
print("\nFlood class distribution:")
print(df["flood_class"].value_counts())
print("\nSaved:", OUT)
print("\nNOTE: Low/Medium/High are project-derived risk labels, not official warning categories.")
