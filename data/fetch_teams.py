import csv
import json
import urllib.request
import urllib.parse

GEONAMES_UNAME = open('.geonames_username').read()

def get_zip_coords(zip):
    if (len(zip) == 4):
        zip = "0" + zip
    
    params = (
        ('postalcode', zip),
        ('maxRows', 1),
        ('country', 'US'),
        ('country', 'CA'),
        ('username', GEONAMES_UNAME)
    )
    url = 'http://api.geonames.org/postalCodeSearchJSON?' + urllib.parse.urlencode(params)
    print(url)
    with urllib.request.urlopen(url) as response:
        body = json.load(response)
    postalCodes = body['postalCodes']
    if (len(postalCodes) == 0):
        raise Exception('no postal codes found')
    return (postalCodes[0]['lat'], postalCodes[0]['lng'])

def get_city_coords(city, state):
    # the mlb api thinks worcester is in rhode island
    if (city == 'Worcester' and state == 'RI'):
        state = 'MA'
    
    params = (
        ('q', city + ' ' + state),
        ('type', 'json'),
        ('maxRows', 1),
        ('country', 'US'),
        ('country', 'CA'),
        ('username', GEONAMES_UNAME)
    )
    url = 'http://api.geonames.org/search?' + urllib.parse.urlencode(params)
    print(url)
    with urllib.request.urlopen(url) as response:
        body = json.load(response)
    geo = body['geonames']
    return (geo[0]['lat'], geo[0]['lng'])
    

with open('teams.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(('team_id', 'team', 'level', 'level_display', 
                        'affiliate_id', 'city', 'state', 'latitude', 'longitude'))

    # get MiLB team information
    milb_team_url = 'http://lookup-service-prod.mlb.com/json/named.team_all.bam?'
    params = (
        ('all_star_sw', "'N'"),
        ('active_sw', "'Y'"),
        ('sport_code', "'mlb'"),
        ('sport_code', "'aaa'"),
        ('sport_code', "'aax'"),
        ('sport_code', "'afa'"),
        ('sport_code', "'afx'"),
        ('team_all.col_in', 'team_id'),
        ('team_all.col_in', 'name_display_full'),
        ('team_all.col_in', 'sport_code'),
        ('team_all.col_in', 'sport_code_display'),
        ('team_all.col_in', 'mlb_org_id'),
        ('team_all.col_in', 'state'),
        ('team_all.col_in', 'city'),
        ('team_all.col_in', 'address'),
        ('team_all.col_in', 'venue_name'),
        ('team_all.col_in', 'address_zip')
    )
    with urllib.request.urlopen(milb_team_url + urllib.parse.urlencode(params)) as response:
        body = json.load(response)
    for team in body['team_all']['queryResults']['row']:
        if not team['mlb_org_id']:
            team['mlb_org_id'] = team['team_id']
        try:
            if (not team['address_zip']):
                raise Exception('no zip code')
            (lat, lon) = get_zip_coords(team['address_zip'])
        except:
            (lat, lon) = get_city_coords(team['city'], team['state'])
        writer.writerow((team['team_id'], team['name_display_full'], 
                            team['sport_code'], team['sport_code_display'],
                            team['mlb_org_id'], team['city'], team['state'],
                            lat, lon))
        if team['sport_code'] == 'mlb':
            img_url = f'https://midfield.mlbstatic.com/v1/team/{team["team_id"]}/spots/108'
            print(img_url)
            req = urllib.request.Request(img_url, headers={'User-agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as f:
                with open(f'../img/{team["team_id"]}.png', 'wb') as img:
                    img.write(f.read())
