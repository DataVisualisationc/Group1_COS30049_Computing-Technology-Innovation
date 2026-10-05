from pathlib import Path
from io import StringIO
import re, pandas as pd

ROOT=Path(__file__).resolve().parent
OM=ROOT.parent/"Data"/"Open-Meteo"
WEATHER=OM/"Weather"; SOLAR=OM/"Daily_solar_dewpoint"; CLOUD=OM/"Daily_cloud_humid_pressure"
OUT=ROOT/"dataset"/"temperature_preprocessed.csv"

FEATURES=["shortwave_radiation_sum","sunshine_duration","daylight_duration","cloud_cover_mean","dew_point_2m_mean","month"]
TARGETS=["temperature_2m_max","temperature_2m_min"]

def clean(c): return re.sub(r"\s*\([^)]*\)\s*$","",str(c)).strip()

def read_two(path):
    text=Path(path).read_text(encoding="utf-8-sig",errors="replace")
    parts=re.split(r"\r?\n\s*\r?\n",text,maxsplit=1)
    if len(parts)==1:
        d=pd.read_csv(path); d.columns=[clean(c) for c in d.columns]
        return d.rename(columns={"time":"date","city/town":"town"})
    meta=pd.read_csv(StringIO(parts[0])); daily=pd.read_csv(StringIO(parts[1]))
    meta.columns=[clean(c) for c in meta.columns]; daily.columns=[clean(c) for c in daily.columns]
    meta=meta.rename(columns={"city/town":"town"}); daily=daily.rename(columns={"time":"date"})
    return daily.merge(meta[[c for c in ["location_id","town"] if c in meta]],on="location_id",how="left")

def norm(s):
    s=str(s).lower()
    for x in ["_solar_dewpoint","_cloud_humid_pressure","_weather"]: s=s.replace(x,"")
    return re.sub(r"[^a-z0-9]","",s)

def match(folder,stem):
    target=norm(stem)
    files=list(folder.glob("*.csv"))
    exact=[p for p in files if norm(p.stem)==target]
    if exact:return exact[0]
    near=[p for p in files if target in norm(p.stem)]
    return near[0] if near else None

def main():
    (ROOT/"dataset").mkdir(exist_ok=True)
    cloud_files=list(CLOUD.glob("*.csv"))
    national=[]
    for p in cloud_files:
        try:
            d=read_two(p); d.columns=[clean(c) for c in d.columns]
            if "cloud_cover_mean" in d and "prefecture" in d:
                d["date"]=pd.to_datetime(d["date"],errors="coerce"); national.append(d)
        except Exception: pass
    national=pd.concat(national,ignore_index=True) if national else None

    outputs=[]
    for wp in sorted(WEATHER.glob("*.csv")):
        pref=wp.stem; sp=match(SOLAR,pref)
        if not sp:
            print(f"SKIP {pref}: solar/dewpoint file not found"); continue
        try:
            w=read_two(wp); s=read_two(sp)
            w["date"]=pd.to_datetime(w["date"],errors="coerce"); s["date"]=pd.to_datetime(s["date"],errors="coerce")
            w["prefecture"]=pref; s["prefecture"]=pref
            wc=["prefecture","location_id","date","town","temperature_2m_max","temperature_2m_min"]
            sc=["prefecture","location_id","date","shortwave_radiation_sum","sunshine_duration","daylight_duration","dew_point_2m_mean"]
            missing_weather = [c for c in wc if c not in w.columns]
            missing_solar = [c for c in sc if c not in s.columns]

            if missing_weather or missing_solar:
                print(f"SKIP {pref}:")
                print(f"  Missing Weather columns: {missing_weather}")
                print(f"  Missing Solar columns:   {missing_solar}")
                continue
            m=w[wc].merge(s[sc],on=["prefecture","location_id","date"],how="inner")
            if national is not None:
                c=national[national["prefecture"].astype(str).str.lower()==pref.lower()]
            else:
                cp=match(CLOUD,pref)
                c=read_two(cp) if cp else None
                if c is not None:c["date"]=pd.to_datetime(c["date"],errors="coerce")
            if c is None or "cloud_cover_mean" not in c:
                print(f"SKIP {pref}: cloud data not found"); continue
            if "location_id" in c:
                m=m.merge(c[["location_id","date","cloud_cover_mean"]],on=["location_id","date"],how="inner")
            elif "town" in c:
                m=m.merge(c[["town","date","cloud_cover_mean"]],on=["town","date"],how="inner")
            else: continue
            m["month"]=m["date"].dt.month
            for col in FEATURES+TARGETS:m[col]=pd.to_numeric(m[col],errors="coerce")
            m=m.dropna(subset=FEATURES+TARGETS)
            outputs.append(m); print(f"OK {pref}: {len(m):,} rows")
        except Exception as e: print(f"SKIP {pref}: {e}")
    if not outputs: raise RuntimeError("No datasets were merged.")
    final=pd.concat(outputs,ignore_index=True).sort_values(["date","prefecture","location_id"])
    final=final[["prefecture","town","location_id","date"]+FEATURES+TARGETS]
    final.to_csv(OUT,index=False,encoding="utf-8-sig")
    print(f"\nSaved {len(final):,} rows -> {OUT}")

if __name__=="__main__": main()
