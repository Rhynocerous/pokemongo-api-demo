
from __future__ import print_function
import requests
import re
import struct
import json
import argparse
import pokemon_pb2
import time
import collections
from collections import namedtuple

from google.protobuf.internal import encoder

from datetime import datetime
from geopy.geocoders import GoogleV3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from s2sphere import *

def encode(cellid):
    output = []
    encoder._VarintEncoder()(output.append, cellid)
    return ''.join(output)

def getNeighbors():
    origin = CellId.from_lat_lng(LatLng.from_degrees(FLOAT_LAT, FLOAT_LONG)).parent(15)
    walk = [origin.id()]
    # 10 before and 10 after
    next = origin.next()
    prev = origin.prev()
    for i in range(10):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return walk

# Added

class Friend:
    def __init__(self,name,wanted):
        self.name = name
        self.wanted = wanted
        
with open('rares.txt') as f:
        RARE_LIST = [line.rstrip('\n') for line in f]
SKIP_LIST = ['Pidgey','Rattata','Weedle','Oddish','Caterpie','Spearow','Zubat','Drowzee','Metapod','Pidgeotto','Pidgeot','Kakuna']
MAP_LIST = ['Golduck','Aerodactyl','Alakazam','Arbok','Arcanine','Articuno','Blastoise','Chansey','Charizard','Charmeleon','Clefable','Dewgong','Ditto','Dodrio','Dragonair','Dragonite','Dratini','Dugtrio','Electrode','Exeggutor','Farfetchd','Gengar','Golduck','Golem','Gyarados','Haunter','Ivysaur','Kabuto','Kabutops','Kadabra','Kangaskhan','Koffing','Lapras','Lickitung','Machamp','Magmar','Magneton','Marowak','Mew','Mewtwo','Moltres','Mr. Mime','Muk','Nidoking','Nidoqueen','Nidorino','Ninetales','Omanyte','Omastar','Persian','Poliwrath','Porygon','Primeape','Rapidash','Rhydon','Sandslash','Slowbro','Snorlax','Tangela','Venusaur','Victreebel','Vileplume','Wartortle','Weezing','Wigglytuff','Zapdos']
HOT_LIST = ['Aerodactyl','Alakazam','Arbok','Arcanine','Articuno','Blastoise','Chansey','Charizard','Clefable','Dewgong','Ditto','Dodrio','Dragonair','Dragonite','Dratini','Dugtrio','Electrode','Exeggutor','Farfetchd','Gengar','Golem','Gyarados','Kabutops','Kangaskhan','Lapras','Lickitung','Machamp','Magmar','Magneton','Marowak','Mew','Mewtwo','Moltres','Mr. Mime','Muk','Nidoking','Nidoqueen','Ninetales','Omastar','Persian','Poliwrath','Porygon','Primeape','Rapidash','Rhydon','Sandslash','Slowbro','Snorlax','Tangela','Venusaur','Victreebel','Vileplume','Wartortle','Weezing','Wigglytuff','Zapdos']

STEPS_BETWEEN_UPDATES = 3

from ast import literal_eval
def get_list(filename):
    wants = []
    with open(filename) as f:
        wants = [line.rstrip('\n') for line in f]
        print(wants)
    return wants
    


import pyshorteners
import webbrowser
import fbchat
from pyshorteners import Shortener

friends = []
url_api_key = 'key'    

# Facebook Alerts
##FB_USERNAME = "FBU"
##FB_PASSWORD = "FBP"
##
##friends.append(Friend("unique url",get_list('wantlist.txt')))

##while 1:
##    try:
##        client = fbchat.Client(FB_USERNAME, FB_PASSWORD)
##        break
##    except:
##        continue
    
##def message_alert(name,lat,lon,dur):
##    for friend in friends:
##        if name in friend.wanted:
##            friend_search = client.getUsers(friend.name)
##            f = friend_search[0]
##            message = '{} found, appearing for {}s at https://www.google.com/maps/place/{},{}'.format(name,dur,lat,lon)
##            sent = client.send(f.uid,message)

# Map Generation

from subprocess import Popen

poke = namedtuple("LabelStruct", ["coords","name","image","vanish_time","vanish_epoch","static_flag"])
class Map(object):
    def __init__(self,lat,lon):
        self._points = []
        self.centerLat = lat
        self.centerLon = lon
    def add_point(self, coordinates, num, name, time_left,static_flag):
        image = 'http://sprites.pokecheck.org/i/'+str(num).zfill(3)+ '.gif'
        #image = 'http://www.pokestadium.com/sprites/black-white/' + str(name).lower() + '.png'
        #image = 'http://www.serebii.net/pokedex-xy/icon/' + str(num).zfill(3) + '.png'
        vanish_time = time.strftime("%I:%M:%S %p",time.localtime(time.time()+time_left))
        vanish_epoch = time.time()+time_left
        self._points.append(poke(coordinates,'none',image,vanish_time,vanish_epoch,static_flag))
    def cleanup(self):
        self._points = [i for i in self._points if i.vanish_epoch > time.time()]
    def __str__(self):
        self.cleanup()
        centerLat = self.centerLat
        centerLon = self.centerLon        
        markersCode = "\n".join(
            [ """var marker{ind} = new google.maps.Marker({{
                position: new google.maps.LatLng({lat}, {lon}),
                map: map,
                icon: '{image}',
                optimized:{static_flag},
                size: new google.maps.Size(300,300)
                }});
                var infowindow{ind} = new google.maps.InfoWindow({{
                content: 'Leaving at {time}'
                }});
                marker{ind}.addListener('click',function() {{
                infowindow{ind}.open(map, marker{ind});
                }});""".format(lat=x.coords[0], lon=x.coords[1],image=x.image,ind=ind,time=x.vanish_time,static_flag=x.static_flag) for ind, x in enumerate(self._points)
            ])
        raresCode = "\n".join(
            [ """new google.maps.Marker({{
                position: new google.maps.LatLng({lat}, {lon}),
                map: map,
                title: '{name}',
                label: '{init}'
                }});""".format(lat=x.coords[0], lon=x.coords[1],name=x.name,init=x.name[0]) for x in self._rares
            ])
        return """
            <meta name="viewport" content="width=device-width">
            <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&sensor=false"></script>
            <div id="map-canvas" style="height: 100%; width: 100%"></div>
            <script type="text/javascript">
                var map;
                function show_map() {{
                    map = new google.maps.Map(document.getElementById("map-canvas"), {{
                        zoom: 16,
                        center: new google.maps.LatLng({centerLat}, {centerLon})
                    }});
                    {markersCode}
                    {raresCode}
                }}
                google.maps.event.addDomListener(window, 'load', show_map);
            </script>
        """.format(centerLat=centerLat, centerLon=centerLon,
                   markersCode=markersCode, raresCode=raresCode)

    
# API
API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'
LOGIN_URL = 'https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'
SESSION = requests.session()
SESSION.headers.update({'User-Agent': 'Niantic App'})
SESSION.verify = False
DEBUG = False
COORDS_LATITUDE = 0 # Can clean this up
COORDS_LONGITUDE = 0
COORDS_ALTITUDE = 0
FLOAT_LAT = 0
FLOAT_LONG = 0

def f2i(float):
  return struct.unpack('<Q', struct.pack('<d', float))[0]

def f2h(float):
  return hex(struct.unpack('<Q', struct.pack('<d', float))[0])

def h2f(hex):
  return struct.unpack('<d', struct.pack('<Q', int(hex,16)))[0]

def set_location(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name)

    print('[!] Your given location: {}'.format(loc.address.encode('utf-8')))
    print('[!] lat/long/alt: {} {} {}'.format(loc.latitude, loc.longitude, loc.altitude))
    set_location_coords(loc.latitude, loc.longitude, loc.altitude)

def set_location_coords(lat, long, alt):
    global COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE
    global FLOAT_LAT, FLOAT_LONG
    FLOAT_LAT = lat
    FLOAT_LONG = long
    COORDS_LATITUDE = f2i(lat) # 0x4042bd7c00000000 # f2i(lat)
    COORDS_LONGITUDE = f2i(long) # 0xc05e8aae40000000 #f2i(long)
    COORDS_ALTITUDE = f2i(alt)

def get_location_coords():
    return (COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE)

def api_req(api_endpoint, access_token, *mehs, **kw):
    try:
        p_req = pokemon_pb2.RequestEnvelop()
        p_req.rpc_id = 1469378659230941192

        p_req.unknown1 = 2

        p_req.latitude, p_req.longitude, p_req.altitude = get_location_coords()

        p_req.unknown12 = 989

        if 'useauth' not in kw or not kw['useauth']:
            p_req.auth.provider = 'ptc'
            p_req.auth.token.contents = access_token
            p_req.auth.token.unknown13 = 14
        else:
            p_req.unknown11.unknown71 = kw['useauth'].unknown71
            p_req.unknown11.unknown72 = kw['useauth'].unknown72
            p_req.unknown11.unknown73 = kw['useauth'].unknown73

        for meh in mehs:
            p_req.MergeFrom(meh)

        protobuf = p_req.SerializeToString()

        r = SESSION.post(api_endpoint, data=protobuf, verify=False)

        p_ret = pokemon_pb2.ResponseEnvelop()
        p_ret.ParseFromString(r.content)

        if DEBUG:
            print("REQUEST:")
            print(p_req)
            print("Response:")
            print(p_ret)
            print("\n\n")

        #print("Sleeping for 1 seconds to get around rate-limit.")
        time.sleep(1)
        return p_ret
    except Exception, e:
        if DEBUG:
            print(e)
        return None

def get_profile(access_token, api, useauth, *reqq):
    req = pokemon_pb2.RequestEnvelop()

    req1 = req.requests.add()
    req1.type = 2
    if len(reqq) >= 1:
        req1.MergeFrom(reqq[0])

    req2 = req.requests.add()
    req2.type = 126
    if len(reqq) >= 2:
        req2.MergeFrom(reqq[1])

    req3 = req.requests.add()
    req3.type = 4
    if len(reqq) >= 3:
        req3.MergeFrom(reqq[2])

    req4 = req.requests.add()
    req4.type = 129
    if len(reqq) >= 4:
        req4.MergeFrom(reqq[3])

    req5 = req.requests.add()
    req5.type = 5
    if len(reqq) >= 5:
        req5.MergeFrom(reqq[4])

    return api_req(api, access_token, req, useauth = useauth)

def get_api_endpoint(access_token, api = API_URL):
    p_ret = get_profile(access_token, api, None)
    try:
        return ('https://%s/rpc' % p_ret.api_url)
    except:
        return None

def login_ptc(username, password):
    print('[!] login for: {}'.format(username))
    head = {'User-Agent': 'niantic'}
    r = SESSION.get(LOGIN_URL, headers=head)
    jdata = json.loads(r.content)
    data = {
        'lt': jdata['lt'],
        'execution': jdata['execution'],
        '_eventId': 'submit',
        'username': username,
        'password': password,
    }
    r1 = SESSION.post(LOGIN_URL, data=data, headers=head)

    ticket = None
    try:
        ticket = re.sub('.*ticket=', '', r1.history[0].headers['Location'])
    except:
        if DEBUG:
            print(r1.json()['errors'][0])
        return None

    data1 = {
        'client_id': 'mobile-app_pokemon-go',
        'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
        'client_secret': 'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR',
        'grant_type': 'refresh_token',
        'code': ticket,
    }
    r2 = SESSION.post(LOGIN_OAUTH, data=data1)
    access_token = re.sub('&expires.*', '', r2.content)
    access_token = re.sub('.*access_token=', '', access_token)
    return access_token

def heartbeat(api_endpoint, access_token, response):
    m4 = pokemon_pb2.RequestEnvelop.Requests()
    m = pokemon_pb2.RequestEnvelop.MessageSingleInt()
    m.f1 = int(time.time() * 1000)
    m4.message = m.SerializeToString()
    m5 = pokemon_pb2.RequestEnvelop.Requests()
    m = pokemon_pb2.RequestEnvelop.MessageSingleString()
    m.bytes = "05daf51635c82611d1aac95c0b051d3ec088a930"
    m5.message = m.SerializeToString()

    walk = sorted(getNeighbors())

    m1 = pokemon_pb2.RequestEnvelop.Requests()
    m1.type = 106
    m = pokemon_pb2.RequestEnvelop.MessageQuad()
    m.f1 = ''.join(map(encode, walk))
    m.f2 = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
    m.lat = COORDS_LATITUDE
    m.long = COORDS_LONGITUDE
    m1.message = m.SerializeToString()
    response = get_profile(
        access_token,
        api_endpoint,
        response.unknown7,
        m1,
        pokemon_pb2.RequestEnvelop.Requests(),
        m4,
        pokemon_pb2.RequestEnvelop.Requests(),
        m5)
    payload = response.payload[0]
    heartbeat = pokemon_pb2.ResponseEnvelop.HeartbeatPayload()
    heartbeat.ParseFromString(payload)
    return heartbeat

def main():
    pokemons = json.load(open('pokemon.json'))
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="PTC Username", required=True)
    parser.add_argument("-p", "--password", help="PTC Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=False)
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-c", "--coords", help="GPS Co-ordinates", required=False)
    parser.set_defaults(DEBUG=False)
    parser.set_defaults(coords="none")
    args = parser.parse_args()

    if args.debug:
        global DEBUG
        DEBUG = True
        print('[!] DEBUG mode on')

    if not args.coords is "none":
        textpairs = []
        locs = collections.deque()
        with open(args.coords) as f:
            locs = [line.rstrip('\n') for line in f]
        print(locs[0])
        set_location(locs[0])
    else:
        set_location(args.location)

    while True:
        access_token = login_ptc(args.username, args.password)
        if access_token is None:
            print('[-] Wrong username/password')
            return
        print('[+] RPC Session Token: {} ...'.format(access_token[:25]))

        api_endpoint = get_api_endpoint(access_token)
        if api_endpoint is None:
            print('[-] RPC server offline')
            return
        print('[+] Received API endpoint: {}'.format(api_endpoint))

        response = get_profile(access_token, api_endpoint, None)
        if response is not None:
            print('[+] Login successful')

            payload = response.payload[0]
            profile = pokemon_pb2.ResponseEnvelop.ProfilePayload()
            profile.ParseFromString(payload)
            print('[+] Username: {}'.format(profile.profile.username))

            creation_time = datetime.fromtimestamp(int(profile.profile.creation_time)/1000)
            print('[+] You are playing Pokemon Go since: {}'.format(
                creation_time.strftime('%Y-%m-%d %H:%M:%S'),
            ))

            for curr in profile.profile.currency:
                print('[+] {}: {}'.format(curr.type, curr.amount))
            break
        else:
            print('[-] Ooops...')
            continue

    origin = LatLng.from_degrees(FLOAT_LAT, FLOAT_LONG)

    # For Google Maps Static API
    URL = 'https://maps.googleapis.com/maps/api/staticmap?center='+str(FLOAT_LAT)+','+str(FLOAT_LONG) + '&zoom=14&size=1000x1000'
    count = 1

    # Initialize a fresh map
    map = Map(FLOAT_LAT,FLOAT_LONG)

    while True:
        original_lat = FLOAT_LAT
        original_long = FLOAT_LONG
        parent = CellId.from_lat_lng(LatLng.from_degrees(FLOAT_LAT, FLOAT_LONG)).parent(15)
        try:
            h = heartbeat(api_endpoint, access_token, response)
        except:
            continue
        hs = [h]
        seen = set([])
        for child in parent.children():
            latlng = LatLng.from_point(Cell(child).get_center())
            set_location_coords(latlng.lat().degrees, latlng.lng().degrees, 0)
            try:
                hs.append(heartbeat(api_endpoint, access_token, response))
            except:
                continue
        set_location_coords(original_lat, original_long, 0)

        visible = []

        for hh in hs:
            for cell in hh.cells:
                for wild in cell.WildPokemon:
                    hash = wild.SpawnPointId + ':' + str(wild.pokemon.PokemonId)
                    if (hash not in seen):
                        visible.append(wild)
                        seen.add(hash)

        print('')
        for cell in h.cells:
            if cell.NearbyPokemon:
                other = LatLng.from_point(Cell(CellId(cell.S2CellId)).get_center())
                diff = other - origin
                # print(diff)
                difflat = diff.lat().degrees
                difflng = diff.lng().degrees
                direction = (('N' if difflat >= 0 else 'S') if abs(difflat) > 1e-4 else '')  + (('E' if difflng >= 0 else 'W') if abs(difflng) > 1e-4 else '')
                print("Within one step of %s (%sm %s from you):" % (other, int(origin.get_distance(other).radians * 6366468.241830914), direction))
                for poke in cell.NearbyPokemon:
                    print('    (%s) %s' % (poke.PokedexNumber, pokemons[poke.PokedexNumber - 1]['Name']))

        #print('')
        for poke in visible:
            other = LatLng.from_degrees(poke.Latitude, poke.Longitude)
            diff = other - origin
            # print(diff)
            difflat = diff.lat().degrees
            difflng = diff.lng().degrees
            direction = (('N' if difflat >= 0 else 'S') if abs(difflat) > 1e-4 else '')  + (('E' if difflng >= 0 else 'W') if abs(difflng) > 1e-4 else '')

            print("(%s) %s is visible at (%s, %s) for %s seconds (%sm %s from you)" % (poke.pokemon.PokemonId, pokemons[poke.pokemon.PokemonId - 1]['Name'], poke.Latitude, poke.Longitude, poke.TimeTillHiddenMs / 1000, int(origin.get_distance(other).radians * 6366468.241830914), direction))

        #Added
        print('')

        # Map search points for extra monitoring
        #URL+= '&markers=color:blue|' + str(FLOAT_LAT) + ',' + str(FLOAT_LONG)
        
        for poke in visible:
            name = pokemons[poke.pokemon.PokemonId - 1]['Name']
            pid = poke.pokemon.PokemonId
            if name in RARE_LIST:
                map.add_point((poke.Latitude, poke.Longitude),pid,name,poke.TimeTillHiddenMs/1000,'false')
            else:
                map.add_point((poke.Latitude, poke.Longitude),pid,name,poke.TimeTillHiddenMs/1000,'true')
            
            
            if pokemons[poke.pokemon.PokemonId - 1]['Name'] in MAP_LIST:
                key = name[0][0]
                URL+= '&markers=color:red|label:' + key + '|' + str(poke.Latitude) + ',' + str(poke.Longitude)
                print('Found a {}'.format(name))
                # Popup map image
                #shortener = Shortener('Google', url_api_key=url_api_key)
                #webbrowser.open(URL)
            if pokemons[poke.pokemon.PokemonId - 1]['Name'] not in SKIP_LIST:    
                with open("Output.txt", "a") as text_file:
                    text_file.write("{},{},{},{},{}\n".format(name,poke.Latitude,poke.Longitude,poke.TimeTillHiddenMs/1000,time.strftime('%y-%m-%d-%H-%M-%S')))
            message_alert(pokemons[poke.pokemon.PokemonId - 1]['Name'],poke.Latitude,poke.Longitude,poke.TimeTillHiddenMs/1000)

        count+=1
        if count > STEPS_BETWEEN_UPDATES:
            with open("pokemap.html", "w") as out:
                print(map, file=out)
            # Push changes
##            p = Popen("upload.bat")
##            stdout, stderr = p.communicate()
            #print(stdout)
            #print(stderr)
            count=0

        #try:
        #    print str(format(shortener.short(URL)))
        #except:
        #    pass

        #print('')
        walk = getNeighbors()
        if args.coords is "none":
            next = LatLng.from_point(Cell(CellId(walk[4])).get_center())
            set_location_coords(next.lat().degrees, next.lng().degrees, 0)
        else:
            locs = locs[1:] + locs[:1]
            new = locs[0].split(',')
            set_location_coords(float(new[0]),float(new[1]), 0)
        
        #if raw_input('The next cell is located at %s. Keep scanning? [Y/n]' % next) in {'n', 'N'}:
        #    break
        

if __name__ == '__main__':
    main()
