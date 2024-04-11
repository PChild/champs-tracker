import requests
import folium
import datetime
import os

m = folium.Map(location=(36.91443, -76.40804), zoom_start=6)

start_date = datetime.date(2024, 4, 9)
end_date = datetime.date(2024, 4, 22)

days = datetime.date.today().day - start_date.day
date_fmt = "%Y-%m-%dT%H:%M:%SZ"

gpsEvents = []

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
                gpsEvents.append(mark)
                prevLat = roundLat
                prevLon = roundLon


coords = []
for idx, mark in enumerate(gpsEvents):
    lat = mark['Latitude']
    lon = mark['Longitude']

    color = "green"
    if idx > 0:
        color = "blue"
        if idx == len(gpsEvents) - 1:
            color = "red"

    coords.append((lat, lon))

    mark_dt = datetime.datetime.strptime(mark['CreateTime'], date_fmt)
    mark_text = mark_dt.strftime("%m-%d-%y %I:%M %p")

    folium.Marker(
        location=[lat, lon],
        tooltip=mark_text,
        popup=mark_text,
        icon=folium.Icon(color),
    ).add_to(m)

folium.PolyLine(coords, tooltip="Approx Route").add_to(m)

# m.show_in_browser()
m.save("index.html")
