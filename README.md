# Pokemon Go Area Coverage Test with Facebook alerts

* Requires facebook username and password and Pokemon Trainer Club username and password
* Generates an HTML file while I look for hosting
* 

## Usage
python main.py -u PTC_USERNAME -p PTC_PASSWORD -c "coordinates.txt"

coordinates.txt contains GPS co-ordinate data in degrees as: 
lat1,lon1
lat2,lon2
...
latn,latn

The lat1,lon1 is the starting position of the generated html map. 
The search cycles through these co-ordinates repeatedly. 

Facebook alerts require a username and password. 
Add a friend and a wantlist using their unique URL identifier and their wantlist by line (e.g.):
Pidgey
Weedle
Squirtle

Facebook supports messaging yourself. 

## Credits
[Mila432](https://github.com/Mila432/Pokemon_Go_API)
tejado, leejao https://github.com/tejado/pgoapi