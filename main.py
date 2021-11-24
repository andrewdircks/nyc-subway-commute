import os
import json
import random
import requests
import numpy as np
import pandas as pd
import geoplot as gplt
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()

MAPS_API_KEY = os.getenv('MAPS_API_KEY')
DISTANCE_BASE_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
GEOCODE_BASE_URL = 'https://maps.googleapis.com/maps/api/geocode/json?'
URL_SUFFIX = f'units=imperial&key={MAPS_API_KEY}'

_offices_raw = {
    'Jack': 'Wavestone, 130 W 42nd St Floor 17, New York, NY 10036',
    'Andrew': '85 Broad St, New York, NY 10004',
    'Andrew_Brooklyn1': '77 Sands St, Brooklyn, NY 11201',
    'Andrew_Brooklyn2': '195 Montague St, Brooklyn, NY 11201',       # + 8 mins from Brooklyn1
    'Trevor': '350 5th Ave #5100, New York, NY 10118'
}
offices = {name: requests.utils.quote(_offices_raw[name]) for name in _offices_raw}

nyc = gpd.read_file(gplt.datasets.get_path('nyc_boroughs'))
manhattan = nyc.loc[nyc['BoroName'] == 'Manhattan'].geometry


def origins_from_roommates(roommates):
    return '|'.join([offices[r] for r in roommates])


def format_pts(xs, ys):
    return '|'.join([requests.utils.quote(f'{ys[i]},{xs[i]}') for i in range(len(xs))])


def random_mesh(N, poly):
    xs, ys = [], []
    _len = 0
    minx, miny, maxx, maxy = poly.bounds

    while _len < N:
        pt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(pt):
            xs.append(pt.x)
            ys.append(pt.y)
            _len += 1

    return xs, ys


def geocode(address):
    url = f'{GEOCODE_BASE_URL}address={address}&{URL_SUFFIX}'
    response = requests.request("GET", url, headers={}, data={})
    data = json.loads(response.text)
    lat_lng = data['results'][0]['geometry']['location']
    return lat_lng['lng'], lat_lng['lat']


def get_distance_matrix(origins, destinations, mode='transit', transit_mode='subway'):
    _origins = f'origins={origins}'
    _destinations = f'destinations={destinations}'
    _mode = f'mode={mode}&transit_mode={transit_mode}'

    url = f'{DISTANCE_BASE_URL}{_origins}&{_destinations}&{_mode}&{URL_SUFFIX}'
    response = requests.request("GET", url, headers={}, data={})
    return json.loads(response.text)


def extract_travel_times(ds, norigins, ndestinations):
    times = np.zeros(shape=(norigins, ndestinations))
    for i in range(norigins):
        for j in range(ndestinations):
            times[i][j] = int(ds['rows'][i]['elements'][j]['duration']['value'])
    return times


def batch(roommates, N=10):
    origins = origins_from_roommates(roommates)
    x, y = random_mesh(N, manhattan.iloc[0])
    rand_manhattan = format_pts(x, y)
    ds = get_distance_matrix(origins, rand_manhattan)
    try:
        travel_t = extract_travel_times(ds, len(roommates), N)
        average_travel_t = np.mean(travel_t, axis=0)
        variance_travel_t = np.var(travel_t, axis=0)
        return x, y, average_travel_t, variance_travel_t

    except:
        print(f'Error in request. Response from Maps API: {ds}')
        exit()


def plot_travel_times(xs, ys, ts, ntotal, ax):
    df = pd.DataFrame(
        {
            'geometry': [Point(xs[i], ys[i]) for i in range(ntotal)],
            'TravelTime': [t/60 for t in ts]    # minutes
        }
    )
    travel_times = gpd.GeoDataFrame(df)

    gplt.pointplot(travel_times, ax=ax, hue='TravelTime', legend=True, cmap='hot_r')


def plot_offices(roommates, ax):
    df = pd.DataFrame({
            'geometry': [Point(geocode(offices[r])) for r in roommates],
        })
    gplt.pointplot(gpd.GeoDataFrame(df), ax=ax, zorder=2, marker='*')
    gplt.polyplot(manhattan, ax=ax, zorder=1)


def main():
    roommates = ['Andrew', 'Jack', 'Trevor']
    ntotal, nbatch = 1000, 20
    xs, ys, ts, vs = [], [], [], []
    for _ in range(int(ntotal/nbatch)):
        x, y, t, v = batch(roommates, N=nbatch)
        xs += x
        ys += y
        ts += list(t)
        vs += list(v)

    fig, (ax1, ax2) = plt.subplots(1, 2)
    plot_travel_times(xs, ys, ts, ntotal, ax1)
    plot_travel_times(xs, ys, vs, ntotal, ax2)
    plot_offices(roommates, ax1)
    plot_offices(roommates, ax2)
    ax1.set_title('Average Travel Time (mins)')
    ax2.set_title('Travel Time Variance')
    plt.show()


if __name__ == '__main__':
    main()
