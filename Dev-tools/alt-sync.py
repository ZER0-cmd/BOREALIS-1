import sys
import pandas as pd
import numpy as np

_, ex, gps, out = sys.argv # paths to data

gdf = pd.read_csv(gps)
edf = pd.read_csv(ex)

gdf['lasttime'] = pd.to_datetime(gdf['lasttime'])
edf['datetime'] = pd.to_datetime(edf['lasttime'])

gdf = gdf.sort_values('lasttime')
edf = edf.sort_values('datetime')

interp = np.interp(edf['datetime'].astype('Int64')//1e9, gdf['lasttime'].astype('Int64')//1e9, gdf['altitude'].astype(float))

edf['Elevation_m'] = interp # sync with data analysis
edf.to_csv(out, index=False)
