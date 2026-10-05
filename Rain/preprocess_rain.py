from pathlib import Path
import pandas as pd, numpy as np

R=Path(__file__).resolve().parent; O=R.parent/"Data"/"Open-Meteo"; OUT=R/"dataset"; OUT.mkdir(exist_ok=True)

def load(p):
    """
    Reads Open-Meteo CSV files that may contain:
      1. location metadata table
      2. blank line
      3. daily weather table

    Returns the daily weather table with location metadata merged in.
    """

    import io

    with open(p, "r", encoding="utf-8-sig") as file:
        lines = file.readlines()

    # --------------------------------------------------
    # Find blank line separating metadata and weather
    # --------------------------------------------------

    blank_index = None

    for i, line in enumerate(lines):
        if line.strip() == "":
            blank_index = i
            break

    # --------------------------------------------------
    # Case 1: Open-Meteo two-table CSV
    # --------------------------------------------------

    if blank_index is not None:

        metadata_text = "".join(lines[:blank_index])

        weather_text = "".join(lines[blank_index + 1:])

        metadata = pd.read_csv(
            io.StringIO(metadata_text)
        )

        d = pd.read_csv(
            io.StringIO(weather_text),
            low_memory=False
        )

        # Clean column names
        metadata.columns = [
            str(c).strip().lower().replace(" ", "_")
            for c in metadata.columns
        ]

        d.columns = [
            str(c).strip().lower().replace(" ", "_")
            for c in d.columns
        ]

        # Rename city/town
        if "city/town" in metadata.columns:
            metadata = metadata.rename(
                columns={"city/town": "town"}
            )

        # Merge location information into weather rows
        if "location_id" in d.columns and "location_id" in metadata.columns:

            d = d.merge(
                metadata,
                on="location_id",
                how="left"
            )

    # --------------------------------------------------
    # Case 2: Normal CSV
    # --------------------------------------------------

    else:

        d = pd.read_csv(
            p,
            low_memory=False
        )

        d.columns = [
            str(c).strip().lower().replace(" ", "_")
            for c in d.columns
        ]

    # --------------------------------------------------
    # Standardise column names
    # --------------------------------------------------

    rename_map = {}

    for col in d.columns:

        # Date
        if col == "time":
            rename_map[col] = "date"

        # Rain
        elif col.startswith("rain_sum"):
            rename_map[col] = "rain_sum"

        # Temperature
        elif col.startswith("temperature_2m_max"):
            rename_map[col] = "temperature_2m_max"

        elif col.startswith("temperature_2m_min"):
            rename_map[col] = "temperature_2m_min"

        # Wind
        elif col.startswith("wind_speed_10m_max"):
            rename_map[col] = "wind_speed_10m_max"

        # Humidity
        elif col.startswith("relative_humidity_2m_mean"):
            rename_map[col] = "relative_humidity_2m_mean"

        # Dew point
        elif col.startswith("dew_point_2m_mean"):
            rename_map[col] = "dew_point_2m_mean"

        # Cloud
        elif col.startswith("cloud_cover_mean"):
            rename_map[col] = "cloud_cover_mean"

        # Pressure
        elif col.startswith("pressure_msl_mean"):
            rename_map[col] = "pressure_msl_mean"

        # Solar radiation
        elif col.startswith("shortwave_radiation_sum"):
            rename_map[col] = "shortwave_radiation_sum"

    d = d.rename(columns=rename_map)

    # --------------------------------------------------
    # Convert date
    # --------------------------------------------------

    if "date" in d.columns:

        d["date"] = pd.to_datetime(
            d["date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    return d

def merge(a,b):
 loc=[c for c in ["location_id","town","city","name","prefecture"] if c in a and c in b]; keys=["date"]+loc
 if not loc and b["date"].duplicated().any(): raise ValueError("multiple locations per date with no common location key")
 return a.merge(b[keys+[c for c in b if c not in a]],on=keys,how="left")
cloud=load(next((O/"Daily_cloud_humid_pressure").glob("*.csv")))
frames=[]

for f in sorted((O/"Weather").glob("*.csv")):
 n=f.stem; print("Processing",n); d=load(f)
 if "prefecture" not in d: d["prefecture"]=n
 for p in [O/"Daily_solar_dewpoint"/f"{n}_solar_dewpoint.csv",O/"Daily_surface_pressure_wind_direction"/f"{n}_pressure_wind.csv"]:
  if p.exists(): d=merge(d,load(p))
 c=cloud
 if "prefecture" in c: c=c[c.prefecture.astype(str).str.casefold()==n.casefold()]
 try: d=merge(d,c)
 except ValueError as e: print(" cloud merge skipped:",e)
 frames.append(d)

df=pd.concat(frames,ignore_index=True)
rc=[c for c in df if c=="rain_sum" or c.startswith("rain_sum")]


if "rain_sum" not in df:
 if not rc: raise KeyError("rain_sum not found")
 df=df.rename(columns={rc[0]:"rain_sum"})
df["rain_sum"]=pd.to_numeric(df.rain_sum,errors="coerce")
df["month"]=pd.to_datetime(df.date,errors="coerce").dt.month
df["rain_class"]=pd.cut(df.rain_sum,[-np.inf,1,10,100,np.inf],right=False,labels=["No/Minimal Rain","Low","Moderate","High"])
wanted=["date","prefecture","town","location_id","temperature_2m_max","temperature_2m_min","relative_humidity_2m_mean","dew_point_2m_mean","cloud_cover_mean","pressure_msl_mean","wind_speed_10m_max","shortwave_radiation_sum","month","rain_sum","rain_class"]
out=df[[c for c in wanted if c in df]].dropna(subset=["date","rain_sum","rain_class"]).drop_duplicates().sort_values("date")
p=OUT/"rain_preprocessed.csv"; out.to_csv(p,index=False)
print("\nSaved:",p,"\nRows:",len(out),"\n",out.rain_class.value_counts())
