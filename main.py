# System Packages
import time

from platDining.functions import *

if __name__ == "__main__":
    # base variables
    start = time.time()
    main_url = "https://dining-offers-prod.amex.r53.tuimedia.com/api/countries"
    country_url = 'https://dining-offers-prod.amex.r53.tuimedia.com/api/country/{0}/merchants'

    # Get all countries
    countries = getCountries(main_url)

    # Get all different merchants
    merchants = getMerchants(country_url, countries)
    merchants_groups = merchantGroupDivider(merchants)

    # Make full dataset
    merchants.update(merchants_groups)

    a = 0
    # Try to determine coordinates
    for merchant_id in merchants.keys():
        a += 1
        merchant = merchants[merchant_id]
        if 'coordinates' in merchant.keys():
            pass
        else:
            merchants[merchant_id]['coordinates'] = coordinates(merchant)
        if a % 111 == 0:
            print(f'{(a/len(merchants.keys())) * 100}% done')

    # Output the map
    createMap(merchants)

    # Output the file
    with open('output/PlatDining.json', 'w') as fp:
        json.dump(merchants, fp)

    print(time.time() - start)
