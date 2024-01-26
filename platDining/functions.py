import json
import os
import folium
import requests
from duckduckgo_search import DDGS
from folium import plugins
from geopy.geocoders import Nominatim
from time import gmtime, strftime, sleep


def getCountries(main_url: str) -> dict:
    page = requests.get(main_url)
    raw_countries = json.loads(page.text)

    countries = {}
    for continent in raw_countries:
        for country in continent['countries']:
            country['continent_title'] = continent['title']
            country['continent_translations'] = continent['translations']
            countries[country['key']] = country

    return countries


def getMerchants(country_url: str, countries: dict) -> dict:
    merchants = {}

    for country in countries.keys():
        data_url = country_url.format(country)
        page = requests.get(data_url)
        raw_merchants = json.loads(page.text)
        for merchant in raw_merchants:
            merchant['country'] = countries[country]
            if merchant['onlineOnly'] == True:
                merchant['coordinates'] = 'onlineOnly'
            merchants[merchant['id']] = merchant

    return merchants


def merchantGroupDivider(merchants: dict) -> tuple[dict, dict]:
    merchants_groups = {}

    for merchant_id in merchants.keys():
        if merchants[merchant_id]['isMerchantGroup'] == True:
            merchants_group = merchants[merchant_id]['merchants']
            for merchant in merchants_group:
                merchants_groups[merchant['id']] = merchant
            merchants[merchant_id]['coordinates'] = 'MerchantGroup'

    return merchants_groups, merchants


def getLatestData():
    main_url = "https://dining-offers-prod.amex.r53.tuimedia.com/api/countries"
    country_url = 'https://dining-offers-prod.amex.r53.tuimedia.com/api/country/{0}/merchants'

    # Get all countries
    countries = getCountries(main_url)

    # Get all different merchants
    merchants = getMerchants(country_url, countries)
    merchants_groups, merchants = merchantGroupDivider(merchants)

    # Make full dataset
    merchants.update(merchants_groups)

    return merchants


def gettingListOfNewMerchants(merchants: dict) -> tuple[dict, dict]:
    current_working_directory = os.getcwd()
    url ='https://raw.githubusercontent.com/Arjanpeace/platDiningScan/main/output/PlatDining.json'
    old_merchants = requests.get(url).json()

    # Make get new additions
    new_merchants = {}
    for key in merchants.keys():
        if key not in old_merchants.keys():
            new_merchants[key] = merchants[key]

    # Make list of removed Apps
    removed_merchants = {}
    for key in old_merchants.keys():
        if key not in merchants.keys():
            removed_merchants[key] = old_merchants[key]

    # Output the removed file
    with open(f'{current_working_directory}/output/RemovedMerchants.json', 'w') as fp:
        json.dump(removed_merchants, fp)

    return new_merchants, old_merchants


def googleMapsUrl(googleMapsUrl: str) -> str:
    values = googleMapsUrl.split('/@')[1].split(',')
    return str(values[0]) + ', ' + str(values[1])


def googleMapsUrlRequest(googleMapsUrl: str) -> str:
    page = requests.get(googleMapsUrl)
    if '/@' in page.text:
        values = page.text.split('/@')[1].split(',')
        return str(values[0]) + ', ' + str(values[1])
    else:
        return 'nothing found'


def businessData(merchant: dict) -> tuple[str, str, str, str]:
    address = merchant['translations']['en']['address']
    city = merchant['city']['translations']['en']['title']
    postcode = merchant['translations']['en']['postcode']
    telephoneNumber = merchant['businessData']['phone']
    return address, city, postcode, telephoneNumber


def duckDuckSearch(name: str, city: str, postcode: str, telephoneNumber: str, address: str) -> str:
    ddgs = DDGS(timeout=20)
    sleep(10)
    ddg_map = ddgs.maps(name, place=city, postalcode=postcode, max_results=1)

    ddg_result = list(ddg_map)
    if len(ddg_result) > 0:
        return str(ddg_result[0]['latitude']) + ', ' + str(ddg_result[0]['longitude'])

    if telephoneNumber == '':
        ddg_map = ddgs.maps(address, place=city, postalcode=postcode, max_results=1)
    else:
        ddg_map = ddgs.maps(telephoneNumber, place=city, postalcode=postcode, max_results=1)

    ddg_result = list(ddg_map)
    if len(ddg_result) > 0:
        return str(ddg_result[0]['latitude']) + ', ' + str(ddg_result[0]['longitude'])

    else:
        return 'nothing found'


def openStreetMapSearch(name: str, address: str, city: str, postcode: str) -> str:
    geolocator = Nominatim(user_agent="AmexDining", timeout=5)
    address = address.split(',')
    if len(address) == 1:
        search_loc = str(address[0]) + ', ' + str(postcode) + ', ' + city
    else:
        search_loc = str(address[-2]) + ', ' + str(address[-1]) + ', ' + str(postcode) + ', ' + city

    location = geolocator.geocode(search_loc)

    if location == None:
        if '/' in search_loc:
            search_loc = search_loc.split('/')[1]
            location = geolocator.geocode(search_loc)
        elif 'floor' in search_loc.lower():
            search_loc = search_loc.lower().split('floor')[1]
            location = geolocator.geocode(search_loc)
        else:
            if len(address) == 1:
                search_loc = str(address[0]) + ', ' + str(postcode)
            else:
                search_loc = str(address[-2]) + ', ' + str(address[-1]) + ', ' + str(postcode)
            location = geolocator.geocode(search_loc)
    if location == None:
        search_loc = str(address[-1]) + ', ' + str(postcode) + ', ' + city
        location = geolocator.geocode(search_loc)
    if location == None:
        print(name, 'no_location_found')
        return 'no_location_found'
    else:
        return str(location.latitude) + ', ' + str(location.longitude)


def coordinates(merchant: dict) -> str:
    if '/@' in merchant['googleMapsUrl']:
        return googleMapsUrl(merchant['googleMapsUrl'])

    googleMapsUrlRequestOutput = googleMapsUrlRequest(merchant['googleMapsUrl'])
    if googleMapsUrlRequestOutput != 'nothing found':
        return googleMapsUrlRequestOutput

    address, city, postcode, telephoneNumber = businessData(merchant)
    name = merchant['name']
    duckDuckSearchOutput = duckDuckSearch(name, city, postcode, telephoneNumber, address)

    if duckDuckSearchOutput != 'nothing found':
        return duckDuckSearchOutput
    else:
        return openStreetMapSearch(name, address, city, postcode)


def addGoogleTag(m: folium.folium.Map) -> str:
    google_tag_head = """
        <head> 
        
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-LMLZ7ZT66Z"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-LMLZ7ZT66Z');
        </script>
        <link rel="shortcut icon" type="image/png" href="images/icons8-vizsla-64.png">
        
        """

    map_title = "Platinum Dining Map"
    title_html = f'<h2 style="position:absolute;z-index:1000;left:15vw" ><em>{map_title}</em></h2>'
    m.get_root().html.add_child(folium.Element(title_html))

    current_date = strftime("%d %b, %Y", gmtime())
    map_footnote = f'''
            <p style="text-align: center;">Updated on {current_date} by <i>SuveBoom</i>. 
            <a href="https://www.buymeacoffee.com/suveboom" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Thank me!" 
            style="height: 30px !important;width: 110px !important;" ></a>
        '''
    title_html = f'<h4 style="position:absolute;left:10vw"" >{map_footnote}</h4>'
    m.get_root().html.add_child(folium.Element(title_html))

    return m.get_root().render().replace('<head>', google_tag_head)


def createInitialMap() -> folium.folium.Map:
    m = folium.Map(location=[48.864716, 2.349014],
                   zoom_start=4,
                   attributionControl=False)
    plugins.Geocoder(collapsed=True).add_to(m)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(m)

    return m
    
    
def createMap(merchants: dict):
    current_working_directory = os.getcwd()
    iframeHtml = """
            <p style="text-align: center;">
            
            <b>Restaurant:</b> 
            <a href="{1}" target="_blank">{0}</a> 
            <br>
            
            <br>
            <b>Cuisine:</b> {2}  
            </p>
    """

    m = createInitialMap()

    marker_cluster = plugins.MarkerCluster().add_to(m)

    cuisines = []
    restaurants = []
    for key, merchant in merchants.items():
        coordi = merchant['coordinates']
        if ',' in str(coordi):
            website = merchant['businessData']['website']
            name = merchant['name']
            cuisine = merchant['cuisine']['translations']['en']['title']
            coordi = coordi.split(',')
            folium.Marker(location=[
                                    coordi[0],
                                    coordi[1]
                                    ],
                          tags=[cuisine, name],
                          popup=iframeHtml.format(name, website, cuisine)).add_to(marker_cluster)
            cuisines.append(cuisine)
            restaurants.append(name)

    cuisines = sorted(set(cuisines))
    plugins.TagFilterButton(
        data=cuisines,
        clear_text='Cuisines'
    ).add_to(m)

    """
    Filter out second filter for mobile app view

    
    restaurants = sorted(set(restaurants))
    plugins.TagFilterButton(
        data=restaurants,
        clear_text='Names'
    ).add_to(m)

    """

    plugins.LocateControl(position="bottomleft",
                          strings={
                              "title": "See you current location",
                              "popup": "Your position"
                          }
                          ).add_to(m)

    m = addGoogleTag(m)
    text_file = open(f'{current_working_directory}/index.html', "w")
    text_file.write(m)
    text_file.close()

