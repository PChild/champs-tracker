import requests
import folium
import datetime
import os
import json
from git import Repo

run_local = False

m = folium.Map(location=(36.91443, -76.40804), zoom_start=6)

file_name = "champsTracker.json"

gps_events = json.load(open(file_name, 'r'))
report_ids = [mark['ReportID'] for mark in gps_events]

date_fmt = "%Y-%m-%dT%H:%M:%SZ"
short_fmt = "%m-%d-%y %I:%M %p"

start_date = datetime.datetime.strptime(
    gps_events[-1]['CreateTime'], date_fmt)

days = datetime.date.today().day - start_date.day


for i in range(0, days):
    new_date = start_date + datetime.timedelta(i)
    new_dt = new_date.strftime(date_fmt)

    payload = {
        "APIKey": os.getenv("TRAK_KEY"),
        "DeviceID": "167794",
        "DateTime_Start": new_dt,
        "FilterByReceivedTime": False
    }

    r = requests.post(
        "https://api-v3.trak-4.com/gps_report_list", json=payload)

    prevLat = 0
    prevLon = 0

    raw_marks = sorted(r.json()['GPSReports'], key=lambda k: k['CreateTime'])
    for mark in raw_marks:
        lat = mark['Latitude']
        lon = mark['Longitude']

        roundLat = round(lat, 3)
        roundLon = round(lon, 3)

        if prevLat != roundLat and prevLon != roundLon:
            if lat != -360.0:
                if mark['ReportID'] not in report_ids:
                    gps_events.append(mark)
                    report_ids.append(mark['ReportID'])
                    prevLat = roundLat
                    prevLon = roundLon

json.dump(gps_events, open(file_name, 'w'))
coords = []
for idx, mark in enumerate(gps_events):
    lat = mark['Latitude']
    lon = mark['Longitude']

    color = "green"
    if idx > 0:
        color = "blue"
        if idx == len(gps_events) - 1:
            color = "red"

    coords.append((lat, lon))

    mark_dt = datetime.datetime.strptime(
        mark['CreateTime'], date_fmt) - datetime.timedelta(hours=4)
    mark_text = mark_dt.strftime(short_fmt)

    folium.Marker(
        location=[lat, lon],
        tooltip=mark_text,
        popup=mark_text,
        icon=folium.Icon(color),
    ).add_to(m)

folium.PolyLine(coords, tooltip="Approx Route").add_to(m)

lats = [coord[0] for coord in coords]
lons = [coord[1] for coord in coords]

min_lat = min(lats)
max_lat = max(lats)
min_lon = min(lons)
max_lon = max(lons)

m.fit_bounds([(min_lat, min_lon), (max_lat, max_lon)], padding=(50, 50))

if run_local:
    m.show_in_browser()
else:
    m.save("index.html")

    repo = Repo("./")
    diffs = repo.index.diff(None)
    repo.index.add([file.a_path for file in diffs])
    update_str = "Automated update at" + datetime.datetime.now().strftime(short_fmt)
    repo.index.commit(update_str)
    origin = repo.remote(name='origin')
    origin.push()
