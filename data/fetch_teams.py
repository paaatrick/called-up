import csv
import json
import urllib
import xml.etree.ElementTree as ET

GEONAMES_UNAME = open('.geonames_username').read()
GEONAMES_URL = 'http://api.geonames.org/search?'
def get_city_coords(city, state):
    params = (
        ('q', city + ' ' + state),
        ('type', 'json'),
        ('maxRows', 1),
        ('country', 'US'),
        ('country', 'CA'),
        ('username', GEONAMES_UNAME)
    )
    url = GEONAMES_URL + urllib.urlencode(params)
    print url
    response = json.load(urllib.urlopen(url))
    geo = response['geonames']
    return (geo[0]['lat'], geo[0]['lng'])
    

with open('teams.csv', 'wb') as csvfile:
    with open('colors.csv', 'wb') as colors:
        writer = csv.writer(csvfile)
        writer.writerow(('team_id', 'team', 'level', 'level_display', 
                         'affiliate_id', 'city', 'state', 'latitude', 'longitude'))

        color_writer = csv.writer(colors)
        color_writer.writerow(('team_id', 'primary', 'primary_link', 'secondary',
                               'tertiary'))
    
        # get MiLB team information
        # url found through feats of reverse engineering
        milb_team_url = 'http://www.milb.com/data/milb_global_nav_static.json'
        resp = json.load(urllib.urlopen(milb_team_url))
        for team in resp['properties_nav']['team_all']['queryResults']['row']:
            # filter out "Complex and Non-Domestic Leagues"
            if team['league'] in ('MEX', 'AZL', 'GCL', 'DSL', 'VSL'):
                continue
            (lat, lon) = get_city_coords(team['city'], team['state'])
            writer.writerow((team['team_id'], team['name_display_full'], 
                             team['sport_code'], team['sport_code_display'],
                             team['mlb_org_id'], team['city'], team['state'],
                             lat, lon))
    
        # get MLB team information
        mlb_team_url = 'http://www.mlb.com/properties/mlb_properties.xml'
        xml = ET.parse(urllib.urlopen(mlb_team_url))
        for team_el in xml.findall('.//team'):
            team = team_el.attrib
            (lat, lon) = get_city_coords(team['city'], team['state_province'])
            writer.writerow((team['team_id'], team['club_full_name'],
                             'mlb', 'Majors', team['team_id'], team['city'],
                             team['state_province'], lat, lon))
            color_writer.writerow((team['team_id'], team['primary'],
                                   team['primary_link'], team['secondary'], 
                                   team['tertiary']))
            url = 'http://mlb.mlb.com/mlb/images/team_logos/logo_{0}_79x76.jpg'.format(
                team['display_code'])
            print url
            urllib.urlretrieve(url, '../img/{0}.jpg'.format(team['team_id']))
