import requests
import json
# import folium
# from folium.plugins import MarkerCluster
# import geopandas as gpd
import pandas as pd
from geopy.geocoders import Nominatim
from duckduckgo_search import DDGS


def getCountries(main_url: str) -> pd.DataFrame:
    """

    :param main_url:
    :return:
    """

    page = requests.get(main_url)
    countries = json.loads(page.text)
    countries = pd.DataFrame(countries)
    countries = countries.explode('countries')
    countries.reset_index(drop=True,
                          inplace=True)
    countries_ = pd.DataFrame(countries['countries'].values.tolist())

    return pd.concat([countries, countries_], axis=1)


def getMerchants(country_url: str, countryList: list) -> pd.DataFrame:
    """

    :param country_url:
    :param countryList:
    :return:
    """

    data = pd.DataFrame()
    for country in countryList:
        data_url = country_url.format(country)
        page = requests.get(data_url)
        y = json.loads(page.text)
        country_data = pd.DataFrame(y)
        country_data['country'] = country
        data = pd.concat([data, country_data])

    return data.reset_index(drop=True)


def merchantGroupDivider(data: pd.DataFrame) -> pd.DataFrame:
    """

    :param data:
    :return:
    """
    for MerchantGroupIndex in data[data['isMerchantGroup'] == True].index:
        MerchantGroup: object = data.loc[MerchantGroupIndex, 'merchants']
        new_df = pd.DataFrame(MerchantGroup)
        new_df['country'] = data.loc[MerchantGroupIndex, 'country']
        if len(new_df) > 0:
            data = pd.concat([data, new_df])
        else:
            print(MerchantGroupIndex)

    return data.reset_index(drop=True)


def coordinates(x) -> str:
    """

    :param x:
    :return:
    """
    geolocator = Nominatim(user_agent="AmexDining", timeout=5)

    if len(x['merchants']) > 0 or len(str(x['merchants'])) > 4:
        return 'MerchantGroup'
    elif x['onlineOnly'] == True:
        return 'online_only'
    elif '/@' in x['googleMapsUrl']:
        values = x['googleMapsUrl'].split('/@')[1].split(',')
        return str(values[0]) + ', ' + str(values[1])
    else:
        url = x['googleMapsUrl']
        page = requests.get(url)
        if '/@' in page.text:
            values = page.text.split('/@')[1].split(',')
            return str(values[0]) + ', ' + str(values[1])
        else:
            address = x['translations_x']['en']['address']
            city = x['city']['title']
            postcode = x['translations_x']['en']['postcode']
            address = address.split(',')
            telephoneNumber = x['businessData']['phone']

            ddgs = DDGS()
            ddg_map = ddgs.maps(x['name'], place=city, max_results=1)
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

            if len(address) == 1:
                search_loc = str(address[0]) + ', ' + str(postcode) + ', ' + city
            else:
                search_loc = str(address[-2]) + ', ' + str(address[-1]) + ', ' + str(postcode) + ', ' + city

            location = geolocator.geocode(search_loc)

            if location == None:
                if '/' in search_loc:
                    search_loc = search_loc.split('/')[1]
                elif 'floor' in search_loc.lower():
                    search_loc = search_loc.lower().split('floor')[1]
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
                print(x['name'], 'no_location_found')
                return 'no_location_found'

            else:
                return str(location.latitude) + ', ' + str(location.longitude)
