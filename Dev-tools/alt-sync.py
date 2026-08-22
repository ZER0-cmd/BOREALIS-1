from datetime import datetime
import os
import sys
import pandas as pd
import numpy as np

_, ex, gps, out = sys.argv # paths to data

os.makedirs(out, exist_ok=True)

gdf = pd.read_csv(gps)

def daytime(df):
    return (
        df.dt.hour * 3600
        + df.dt.minute * 60
        + df.dt.second
        + df.dt.microsecond * 1e-6
    )


gdf['lasttime'] = pd.to_datetime(gdf['lasttime'])
gdf = gdf.sort_values('lasttime')
gtime = daytime(gdf['lasttime'])
alt = gdf['altitude'].astype(float)

def process(file, output):
    edf = pd.read_csv(file)
    edf['datetime'] = pd.to_datetime(edf['datetime'], format='%Y/%m/%d@%H:%M:%S')
    edf = edf.sort_values('datetime')
    etime = daytime(edf['datetime'])

    mask = (etime >= gtime.min()) & (etime <= gtime.max())
    edf = edf[mask]
    etime = etime[mask]

    interp = np.interp(etime, gtime, alt, left=0, right=0)

    edf['Elevation_m'] = interp  # sync with data analysis
    if edf.empty:
        raise ValueError("No data in GPS time range")
    edf['datetime'] = edf['datetime'].dt.strftime('%Y/%m/%d@%H:%M:%S')
    edf.to_csv(output, index=False)

for root, dirs, files in os.walk(ex):
    if 'SD-CARD (ALL CONTENT)' in root: # Skips raw files. Change if needed
        continue
    rroot = os.path.relpath(root, ex)
    droot = out if rroot == '.' else os.path.join(out, rroot)
    os.makedirs(droot, exist_ok=True)

    for fname in files:
        if not fname.endswith('.csv'):
            continue
        src = os.path.join(root, fname)
        dst = os.path.join(droot, fname)

        print(f"Processing: {os.path.relpath(src, ex)}")
        try:
            process(src, dst)
        except Exception as e:
            print(f"Error: {e}")

print("Done")
