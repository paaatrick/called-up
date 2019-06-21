import csv
import json
import urllib
import xml.etree.ElementTree as ET

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
    url = 'http://api.geonames.org/postalCodeSearchJSON?' + urllib.urlencode(params)
    print url
    response = json.load(urllib.urlopen(url))
    postalCodes = response['postalCodes']
    if (len(postalCodes) == 0):
        raise Exception('no postal codes found')
    return (postalCodes[0]['lat'], postalCodes[0]['lng'])

def get_city_coords(city, state):
    params = (
        ('q', city + ' ' + state),
        ('type', 'json'),
        ('maxRows', 1),
        ('country', 'US'),
        ('country', 'CA'),
        ('username', GEONAMES_UNAME)
    )
    url = 'http://api.geonames.org/search?' + urllib.urlencode(params)
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
        milb_team_url = 'http://lookup-service-prod.mlb.com/json/named.team_all.bam?'
        params = (
            ('all_star_sw', "'N'"),
            ('active_sw', "'Y'"),
            ('league', "'INT'"),
            ('league', "'PCL'"),
            ('league', "'EAS'"),
            ('league', "'SOU'"),
            ('league', "'TEX'"),
            ('league', "'CAL'"),
            ('league', "'CAR'"),
            ('league', "'FSL'"),
            ('league', "'MID'"),
            ('league', "'SAL'"),
            ('league', "'NWL'"),
            ('league', "'NYP'"),
            ('league', "'APP'"),
            ('league', "'PIO'"),
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
        resp = json.load(urllib.urlopen(milb_team_url + urllib.urlencode(params)))
        for team in resp['team_all']['queryResults']['row']:
            if not team['mlb_org_id']:
                continue
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
