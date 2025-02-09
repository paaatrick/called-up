import csv
import datetime
import json
import os
import urllib.request
import urllib.parse


HERE = os.path.abspath(os.path.dirname(__file__))
SPORT_IDS = "1,11,12,13,14"
SEASON = datetime.date.today().year


def get(url, params):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as response:
        return json.load(response)


venues = get(
    "https://statsapi.mlb.com/api/v1/venues",
    {"sportIds": SPORT_IDS, "season": SEASON, "hydrate": "location"},
)
venues_by_id = {v["id"]: v for v in venues["venues"]}

teams = get(
    "https://statsapi.mlb.com/api/v1/teams",
    {
        "sportIds": SPORT_IDS,
        "season": SEASON,
        "hydrate": "sport",
    },
)

with open(f"{HERE}/teams.csv", "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(
        (
            "team_id",
            "team",
            "level",
            "level_display",
            "affiliate_id",
            "city",
            "state",
            "latitude",
            "longitude",
        )
    )
    for team in teams["teams"]:
        venue = venues_by_id[team["venue"]["id"]]
        location = venue["location"]
        coords = location["defaultCoordinates"]
        latitude = coords["latitude"]
        longitude = coords["longitude"]
        if latitude < 0:
            # It looks like lat and lon got switched for some teams
            latitude, longitude = longitude, latitude

        writer.writerow(
            (
                team["id"],
                team["name"],
                team["sport"]["code"],
                team["sport"]["abbreviation"],
                team.get("parentOrgId", team["id"]),
                location["city"],
                location["stateAbbrev"],
                latitude,
                longitude,
            )
        )
        if team["sport"]["code"] == "mlb":
            img_url = f"https://www.mlbstatic.com/team-logos/{team['id']}.svg"
            req = urllib.request.Request(img_url, headers={"User-agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as f:
                with open(f"{HERE}/../img/{team['id']}.svg", "wb") as img:
                    img.write(f.read())
