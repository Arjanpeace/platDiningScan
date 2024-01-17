import json

import folium
import requests
from duckduckgo_search import DDGS
from folium import plugins
from geopy.geocoders import Nominatim


def getCountries(main_url: str):
    page = requests.get(main_url)
    raw_countries = json.loads(page.text)

    countries = {}
    for continent in raw_countries:
        for country in continent['countries']:
            country['continent_title'] = continent['title']
            country['continent_translations'] = continent['translations']
            countries[country['key']] = country

    return countries


def getMerchants(country_url: str, countries):
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


def merchantGroupDivider(merchants):
    merchants_groups = {}

    for merchant_id in merchants.keys():
        if merchants[merchant_id]['isMerchantGroup'] == True:
            merchants_group = merchants[merchant_id]['merchants']
            for merchant in merchants_group:
                merchants_groups[merchant['id']] = merchant
            merchants[merchant_id]['coordinates'] = 'MerchantGroup'

    return merchants_groups


def googleMapsUrl(googleMapsUrl):
    values = googleMapsUrl.split('/@')[1].split(',')
    return str(values[0]) + ', ' + str(values[1])


def googleMapsUrlRequest(googleMapsUrl):
    page = requests.get(googleMapsUrl)
    if '/@' in page.text:
        values = page.text.split('/@')[1].split(',')
        return str(values[0]) + ', ' + str(values[1])
    else:
        return 'nothing found'


def businessData(merchant):
    address = merchant['translations']['en']['address']
    city = merchant['city']['translations']['en']['title']
    postcode = merchant['translations']['en']['postcode']
    telephoneNumber = merchant['businessData']['phone']
    return address, city, postcode, telephoneNumber


def duckDuckSearch(name, city, postcode, telephoneNumber, address):
    ddgs = DDGS()
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


def openStreetMapSearch(name, address, city, postcode):
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


def coordinates(merchant):
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


def createMap(merchants):
    html = """
   <a href="{1}" target="_blank">{0}</a> 
    """

    m = folium.Map(location=[48.864716, 2.349014], zoom_start=3,
                   control_scale=True)

    plugins.Geocoder().add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)

    cuisines = []
    for key, merchant in merchants.items():
        coordi = merchant['coordinates']
        if ',' in str(coordi):
            website = merchant['businessData']['website']
            name = merchant['name']
            cuisine = merchant['cuisine']['translations']['en']['title']
            coordi = coordi.split(',')
            folium.Marker(location=[coordi[0],
                                    coordi[1]
                                    ],
                          tags=[cuisine],
                          popup=html.format(name, website)).add_to(m)
            cuisines.append(cuisine)

    cuisines = list(set(cuisines))
    plugins.TagFilterButton(
        data=cuisines,
        clear_text='Remove Filter'
    ).add_to(m)

    m.save("output/index.html")
