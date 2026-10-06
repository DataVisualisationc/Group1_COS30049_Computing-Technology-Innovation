from pathlib import Path
import io
import pandas as pd

ROOT = Path(__file__).resolve().parent
OPEN_METEO = ROOT.parent / "Data" / "Open-Meteo"
WEATHER_DIR = OPEN_METEO / "Weather"
PRESSURE_DIR = OPEN_METEO / "Daily_surface_pressure_wind_direction"
OUT_DIR = ROOT / "dataset"
OUT_DIR.mkdir(exist_ok=True)

def clean_name(c):
    return str(c).strip().lower().replace(" ", "_")

def load_openmeteo(path):
    """Read Open-Meteo files containing metadata + blank line + daily table."""
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    blank = next((i for i, line in enumerate(lines) if line.strip() == ""), None)

    if blank is not None:
        meta = pd.read_csv(io.StringIO("".join(lines[:blank])))
        data = pd.read_csv(io.StringIO("".join(lines[blank+1:])), low_memory=False)

        meta.columns = [clean_name(c) for c in meta.columns]
        data.columns = [clean_name(c) for c in data.columns]

        if "city/town" in meta.columns:
            meta = meta.rename(columns={"city/town": "town"})

        if "location_id" in meta.columns and "location_id" in data.columns:
            # Keep useful location metadata but avoid duplicate weather columns.
            keep = [c for c in ["location_id", "town", "latitude", "longitude"] if c in meta.columns]
            data = data.merge(meta[keep], on="location_id", how="left")
    else:
        data = pd.read_csv(path, low_memory=False)
        data.columns = [clean_name(c) for c in data.columns]

    rename = {}
    for c in data.columns:
        if c == "time":
            rename[c] = "date"
        elif c.startswith("surface_pressure_mean"):
            rename[c] = "surface_pressure_mean"
        elif c.startswith("surface_pressure_max"):
            rename[c] = "surface_pressure_max"
        elif c.startswith("surface_pressure_min"):
            rename[c] = "surface_pressure_min"
        elif c.startswith("wind_direction_10m_dominant"):
            rename[c] = "wind_direction_10m_dominant"
        elif c.startswith("wind_speed_10m_max"):
            rename[c] = "wind_speed_10m_max"

    data = data.rename(columns=rename)
    if "date" in data.columns:
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
    return data

def merge_sources(weather, pressure):
    keys = ["location_id", "date"]
    missing = [k for k in keys if k not in weather.columns or k not in pressure.columns]
    if missing:
        raise KeyError(f"Cannot merge: missing merge key(s) {missing}")

    needed = [
        "location_id", "date",
        "surface_pressure_mean", "surface_pressure_max", "surface_pressure_min",
        "wind_direction_10m_dominant"
    ]
    absent = [c for c in needed if c not in pressure.columns]
    if absent:
        raise KeyError(f"Pressure/wind-direction source missing columns: {absent}")

    return weather.merge(
        pressure[needed].drop_duplicates(keys),
        on=keys,
        how="inner",
        validate="m:1"
    )

frames = []
weather_files = sorted(WEATHER_DIR.glob("*.csv"))
if not weather_files:
    raise FileNotFoundError(f"No files found in {WEATHER_DIR}")

for wf in weather_files:
    prefecture = wf.stem
    pf = PRESSURE_DIR / f"{prefecture}_pressure_wind.csv"

    if not pf.exists():
        print(f"SKIP {prefecture}: {pf.name} not found")
        continue

    print(f"Processing {prefecture}...")
    w = load_openmeteo(wf)
    p = load_openmeteo(pf)

    if "wind_speed_10m_max" not in w.columns:
        print(f"  SKIP: wind_speed_10m_max not found in {wf.name}")
        continue

    merged = merge_sources(w, p)
    merged["prefecture"] = prefecture
    frames.append(merged)

if not frames:
    raise RuntimeError("No prefecture datasets could be merged.")

df = pd.concat(frames, ignore_index=True)
df = df.sort_values(["prefecture", "location_id", "date"])

# Created feature: today's mean pressure minus previous day's mean pressure,
# separately for each physical location.
df["pressure_change"] = (
    df.groupby(["prefecture", "location_id"])["surface_pressure_mean"].diff()
)

FEATURES = [
    "surface_pressure_mean",
    "surface_pressure_max",
    "surface_pressure_min",
    "pressure_change",
    "wind_direction_10m_dominant",
]
TARGET = "wind_speed_10m_max"

for c in FEATURES + [TARGET]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

before = len(df)
df = df.dropna(subset=["date"] + FEATURES + [TARGET]).copy()
df = df.drop_duplicates(subset=["prefecture", "location_id", "date"])

columns = [
    "date", "prefecture", "location_id", "town",
    *FEATURES, TARGET
]
columns = [c for c in columns if c in df.columns]
df = df[columns].sort_values(["date", "prefecture", "location_id"])

out = OUT_DIR / "wind_preprocessed.csv"
df.to_csv(out, index=False)

print("\n" + "="*65)
print("WIND PREPROCESSING COMPLETE")
print("="*65)
print(f"Rows before final cleaning : {before:,}")
print(f"Rows saved                 : {len(df):,}")
print(f"Date range                 : {df['date'].min().date()} -> {df['date'].max().date()}")
print(f"Target                     : {TARGET} (km/h)")
print(f"Output                     : {out}")
print("\nTarget summary:")
print(df[TARGET].describe())
