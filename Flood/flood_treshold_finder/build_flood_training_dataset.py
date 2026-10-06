import pandas as pd
import numpy as np
import requests, time, random
from datetime import timedelta

INPUT = "jpn_glide_events.csv"
OUTPUT = "japan_flood_training_dataset.csv"
WEATHER='https://archive-api.open-meteo.com/v1/archive'
FLOOD='https://flood-api.open-meteo.com/v1/flood'
SEED=42
random.seed(SEED)

raw=pd.read_csv(INPUT)
f=raw[raw['event'].eq('FL')].copy()
f=f[f['month'].between(1,12)&f['day'].between(1,31)]
f=f[f['latitude'].between(-90,90)&f['longitude'].between(-180,180)]
f=f[~((f['latitude']==0)&(f['longitude']==0))].copy()
f['event_date']=pd.to_datetime(dict(year=f.year,month=f.month,day=f.day),errors='coerce')
f=f.dropna(subset=['event_date']).reset_index(drop=True)

# all known valid flood dates, used to avoid negative anchors near a known flood
known_dates=set(f['event_date'].dt.date)

def near_known_flood(d, days=14):
    return any(abs((d-k).days)<=days for k in known_dates)

def choose_negative(event_date):
    # deterministic seasonal-ish candidates, 30-90 days from event
    offsets=[-45,45,-60,60,-75,75,-90,90,30,-30]
    for off in offsets:
        d=(event_date+pd.Timedelta(days=off)).date()
        if not near_known_flood(d,14): return pd.Timestamp(d)
    raise RuntimeError('No negative date found')

def get_json(url, params, retries=4):
    for i in range(retries):
        try:
            r=requests.get(url,params=params,timeout=60)
            r.raise_for_status(); return r.json()
        except Exception:
            if i==retries-1: raise
            time.sleep(2*(i+1))

def features(lat,lon,anchor):
    # Predict whether flood occurs on anchor using ONLY previous 7 complete days
    start=anchor-pd.Timedelta(days=7); end=anchor-pd.Timedelta(days=1)
    wp={'latitude':lat,'longitude':lon,'start_date':start.strftime('%Y-%m-%d'),'end_date':end.strftime('%Y-%m-%d'),
        'daily':'rain_sum,precipitation_sum,precipitation_hours','timezone':'auto','cell_selection':'nearest'}
    w=get_json(WEATHER,wp)
    fp={'latitude':lat,'longitude':lon,'start_date':start.strftime('%Y-%m-%d'),'end_date':end.strftime('%Y-%m-%d'),
        'daily':'river_discharge','cell_selection':'nearest'}
    q=get_json(FLOOD,fp)
    wd=pd.DataFrame(w['daily']); qd=pd.DataFrame(q['daily'])
    wd['time']=pd.to_datetime(wd['time']); qd['time']=pd.to_datetime(qd['time'])
    d=wd.merge(qd,on='time',how='inner').sort_values('time')
    if len(d)<5: raise ValueError(f'Only {len(d)} matched days')
    rain=pd.to_numeric(d['rain_sum'],errors='coerce')
    precip_hours=pd.to_numeric(d['precipitation_hours'],errors='coerce')
    discharge=pd.to_numeric(d['river_discharge'],errors='coerce')
    last=discharge.iloc[-1]
    four_days_prior=discharge.iloc[-5]
    ratio=np.nan if pd.isna(four_days_prior) or four_days_prior==0 else last/four_days_prior
    return {
        'window_start':start.date(),'window_end':end.date(),
        'rain_sum_past_3day':rain.tail(3).sum(min_count=1),
        'rain_sum_past_7day':rain.sum(min_count=1),
        'max_daily_rain_past_7day':rain.max(),
        'rain_flag_50mm':int((rain>50).any()) if rain.notna().any() else np.nan,
        'precipitation_hours_past_7day':precip_hours.sum(min_count=1),
        'river_discharge':last,
        'river_discharge_mean_7day':discharge.mean(),
        'river_discharge_median_7day':discharge.median(),
        'river_discharge_max_7day':discharge.max(),
        'discharge_ratio':ratio,
        'elevation':w.get('elevation',np.nan),
        'weather_api_latitude':w.get('latitude',np.nan),'weather_api_longitude':w.get('longitude',np.nan),
        'flood_api_latitude':q.get('latitude',np.nan),'flood_api_longitude':q.get('longitude',np.nan),
    }

from concurrent.futures import ThreadPoolExecutor, as_completed

jobs=[]
for i,r in f.iterrows():
    jobs.append((i,r,1,r.event_date,'flood'))
    jobs.append((i,r,0,choose_negative(r.event_date),'non_flood'))

def run_job(job):
    i,r,y,anchor,kind=job
    z=features(r.latitude,r.longitude,anchor)
    return {'source_event':r.glidenumber,'source_location':r.location,'anchor_date':anchor.date(),
            'latitude':r.latitude,'longitude':r.longitude,'sample_type':kind,'flood':y,**z}

rows=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    futs={ex.submit(run_job,j):j for j in jobs}
    for n,fut in enumerate(as_completed(futs),1):
        j=futs[fut]
        try:
            rows.append(fut.result()); print(f'{n}/{len(jobs)} done')
        except Exception as e:
            print('FAILED',j[1].glidenumber,j[4],e)

out=pd.DataFrame(rows)
out.to_csv(OUTPUT,index=False)
print('\nSaved',OUTPUT)
print('rows',len(out)); print(out['flood'].value_counts(dropna=False))
print('\nMissing values:'); print(out.isna().sum().sort_values(ascending=False).head(15))
