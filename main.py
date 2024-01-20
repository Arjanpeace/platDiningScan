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

    with open('output/platDining.json', 'r') as f:
        old_merchants = json.load(f)

    # Make get new additions
    new_merchants = {}
    for key in merchants.keys():
        if key not in old_merchants.keys():
            new_merchants[key] = merchants[key]

    if len(new_merchants.keys()) > 0:
        a = 0
        # Try to determine coordinates
        for merchant_id in new_merchants.keys():
            a += 1
            merchant = new_merchants[merchant_id]
            if 'coordinates' in merchant.keys():
                pass
            else:
                new_merchants[merchant_id]['coordinates'] = coordinates(merchant)
            if a % 111 == 0:
                print(f'{(a/len(new_merchants.keys())) * 100}% done')

        # Make full dataset
        old_merchants.update(new_merchants)

    # Output the map
    createMap(old_merchants)

    # Output the file
    with open('output/PlatDining.json', 'w') as fp:
        json.dump(old_merchants, fp)

    missing = {}
    for key, item in old_merchants.items():
        if item['coordinates'] == 'no_location_found':
            missing[key] = item

    # Output the missing file
    with open('output/PlatDiningMissingCoordinates.json', 'w') as fp:
        json.dump(missing, fp)

    print(time.time() - start)
