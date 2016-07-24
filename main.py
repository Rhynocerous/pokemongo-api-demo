
from __future__ import print_function
import time
from search import *
from collections import namedtuple
import collections
from subprocess import Popen

# Map Generation

poke = namedtuple("LabelStruct", ["coords","name","image","vanish_time","vanish_epoch","static_flag"])
class Map(object):
    def __init__(self,lat,lon,inputs):
        self._points = []
        self.centerLat = lat
        self.centerLon = lon
        self.api = inputs['maps_api_key']
        try:
            self.twilio_inputs = inputs['twilio']
        except KeyError:
            self.twilio_inputs = 'none'
        try:
            self.map_style = inputs['map_style']
        except KeyError:
            self.map_style = []
        try:
            self.style = int(inputs['sprite_style'])
        except KeyError:
            self.style = 1
        try:
            self.domain = inputs['domain_name']
        except KeyError:
            self.domain = 'git.io/vKynk'
    def add_point(self, coordinates, num, name, time_left,static_flag):
        # Don't add pokemon if it's a duplicate (by co-ordinates)
        if any((coordinates == i.coords and name == i.name) for i in self._points):
            return
        if self.style == 2:
            image = 'http://www.pkparaiso.com/imagenes/xy/sprites/animados/' + name.lower() + '.gif'
        elif self.style == 3:
            image = 'http://www.serebii.net/pokedex-xy/icon/' + str(num).zfill(3) + '.png'
        else:
            image = 'http://sprites.pokecheck.org/i/'+str(num).zfill(3)+ '.gif'
        vanish_time = time.strftime("%I:%M:%S %p",time.localtime(time.time()+time_left))
        vanish_epoch = int(time.time()+time_left)
        if vanish_epoch < time.time():
            return
        pokemon_info = poke(coordinates,name,image,vanish_time,vanish_epoch,static_flag)
        if not self.twilio_inputs == 'none':
            global twil
            twil.send_messages(pokemon_info,self.twilio_inputs['recipients'])
        self._points.append(pokemon_info)
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
                content: '<center>{name}<br>Leaving at {time}</center>'
                }});
                marker{ind}.addListener('click',function() {{
                infowindow{ind}.open(map, marker{ind});
                }});""".format(lat=x.coords[0], lon=x.coords[1],image=x.image,ind=ind,time=x.vanish_time,static_flag=x.static_flag,name=x.name) for ind, x in enumerate(self._points)
            ])
        floatboxCode = "\n".join([ """
                <style>
                   #wrapper {{ position: relative; }}
                   #over_map {{ position: fixed; bottom: 0; left: 0; z-index: 99;  border: 2px solid #4d7a1f; background: white; padding: 5px 5px 5px 5px; line-height:20px; height=50px; margin:0; text-align: center;font-size:x-small; font-family:Verdana, Geneva, sans-serif;}}
                </style>

                <div id="over_map">
                Refresh page to update<br>
                <a href = "http://{domain}">Info at {domain}</a>
                </div>
                """.format(domain = self.domain)
            ])
        return """
            {floatboxCode}
            <meta name="viewport" content="width=device-width">
            <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&key={MAPS_API_KEY}"></script>
            <div id="map-canvas" style="height: 100%; width: 100%"></div>
            <script type="text/javascript">
                function show_map() {{
                    map = new google.maps.Map(document.getElementById("map-canvas"), {{
                        zoom: 16,
                        center: new google.maps.LatLng({centerLat}, {centerLon})
                    }});
                    var map;
            var styles={style}
            map.setOptions({{styles: styles}});
                    {markersCode}
                }}
                google.maps.event.addDomListener(window, 'load', show_map);
            </script>
        """.format(centerLat=centerLat, centerLon=centerLon,
                   markersCode=markersCode,MAPS_API_KEY =self.api,style=self.map_style,floatboxCode=floatboxCode)


        

def main():
    
    pokemons = json.load(open('pokemon.json'))
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="PTC Username", required=True)
    parser.add_argument("-p", "--password", help="PTC Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=False)
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-c", "--coords", help="GPS Co-ordinates", required=False)
    parser.add_argument("-i", "--inputs", help="Input JSON file", required=False)
    parser.set_defaults(DEBUG=False)
    parser.set_defaults(coords="none")
    parser.set_defaults(location="none")
    parser.set_defaults(inputs="none")
    args = parser.parse_args()

    if args.inputs is "none":
        inputs = json.load(open('input.json'))
    else:
        try:
            inputs = json.load(open(args.inputs))
        except IOError as err:
            print('Could not find input JSON file, remember the file extension -  ',err)
            return

    if args.debug:
        global DEBUG
        DEBUG = True
        print('[!] DEBUG mode on')

    if args.location is "none":
        locs = collections.deque()
        locs = inputs['search_coords']
        try:
            start_loc = inputs['start_location']
        except KeyError:
            print('Using first search_coord as map center.')
            start_loc = locs[0]
        set_location(start_loc)
        start_lat = float(start_loc.split(',')[0])
        start_lon = float(start_loc.split(',')[1])
    else:
        print('Finding location based on argument input...')
        geoloc_result = set_location(args.location)
        start_lat = float(geoloc_result.latitude)
        start_lon = float(geoloc_result.longitude)

    # Handle Twilio
    try:
        twilio_params = inputs['twilio']
        import notifications
        global twil
        twil = notifications.Notifications(twilio_params['account_sid'],twilio_params['auth_token'],twilio_params['number'])
    except KeyError:
        pass

    origin = LatLng.from_degrees(start_lat,start_lon)

    while True:
        try:
            access_token = login_ptc(args.username, args.password)
        except ValueError:
            print('Login Failed')
            time.sleep(5)
            continue

        if access_token is None:
            print('[-] Wrong username/password')
            return
        print('[+] RPC Session Token: {} ...'.format(access_token[:25]))

        api_endpoint = get_api_endpoint(access_token)
        if api_endpoint is None:
            print('[-] RPC server offline')
            time.sleep(5)
            continue # Try to log in again
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

    # Initialize a fresh map
    map = Map(start_lat,start_lon,inputs)
    while True:
        original_lat,original_long = get_float_coords()
        new_coords = get_float_coords()
        parent = CellId.from_lat_lng(LatLng.from_degrees(new_coords[0],new_coords[1])).parent(15)
        try:
            h = heartbeat(api_endpoint, access_token, response)
        except:
            print('Failed server response, trying again...')
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

##        #print('')
##        for cell in h.cells:
##            if cell.NearbyPokemon:
##                other = LatLng.from_point(Cell(CellId(cell.S2CellId)).get_center())
##                diff = other - origin
##                print(diff)
##                difflat = diff.lat().degrees
##                difflng = diff.lng().degrees
##                direction = (('N' if difflat >= 0 else 'S') if abs(difflat) > 1e-4 else '')  + (('E' if difflng >= 0 else 'W') if abs(difflng) > 1e-4 else '')
##                print("Within one step of %s (%sm %s from you):" % (other, int(origin.get_distance(other).radians * 6366468.241830914), direction))
##                for poke in cell.NearbyPokemon:
##                    print('    (%s) %s' % (poke.PokedexNumber, pokemons[poke.PokedexNumber - 1]['Name']))

##        #print('')
##        for poke in visible:
##            other = LatLng.from_degrees(poke.Latitude, poke.Longitude)
##            diff = other - origin
##            print(diff)
##            difflat = diff.lat().degrees
##            difflng = diff.lng().degrees
##            direction = (('N' if difflat >= 0 else 'S') if abs(difflat) > 1e-4 else '')  + (('E' if difflng >= 0 else 'W') if abs(difflng) > 1e-4 else '')
##            print("(%s) %s is visible at (%s, %s) for %s seconds (%sm %s from you)" % (poke.pokemon.PokemonId, pokemons[poke.pokemon.PokemonId - 1]['Name'], poke.Latitude, poke.Longitude, poke.TimeTillHiddenMs / 1000, int(origin.get_distance(other).radians * 6366468.241830914), direction))

        
        for poke in visible:
            name = pokemons[poke.pokemon.PokemonId - 1]['Name']
            pid = poke.pokemon.PokemonId

            if name in inputs['static_list']:
                map.add_point((poke.Latitude, poke.Longitude),pid,name,poke.TimeTillHiddenMs/1000,'true')
            elif name not in inputs['skip_list']:
                map.add_point((poke.Latitude, poke.Longitude),pid,name,poke.TimeTillHiddenMs/1000,'false')
            #message_alert(pokemons[poke.pokemon.PokemonId - 1]['Name'],poke.Latitude,poke.Longitude,poke.TimeTillHiddenMs/1000)

        with open(inputs['map_directory']+inputs['map_name']+".html", "w") as out:
            print(map, file=out)

        #Search algorithm or specified search pattern
        walk = getNeighbors()
        if args.location is "none":
            locs = locs[1:] + locs[:1]
            new = locs[0].split(',')
            set_location_coords(float(new[0]),float(new[1]), 0)
        else:
            next = LatLng.from_point(Cell(CellId(walk[4])).get_center())
            set_location_coords(next.lat().degrees, next.lng().degrees, 0)

if __name__ == '__main__':
    main()
