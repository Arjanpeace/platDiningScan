# System Packages
import time
import os

from platDining.functions import *

if __name__ == "__main__":
    # base variables
    start = time.time()
    current_working_directory = os.getcwd()
    merchants = getLatestData()
    new_merchants, old_merchants = gettingListOfNewMerchants(merchants)

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
    with open('./output/PlatDining.json', 'w') as fp:
        json.dump(old_merchants, fp)

    missing = {}
    for key, item in old_merchants.items():
        if item['coordinates'] == 'no_location_found':
            missing[key] = item

    # Output the missing file
    with open(f'{current_working_directory}/output/PlatDiningMissingCoordinates.json', 'w') as fp:
        json.dump(missing, fp)

    print(time.time() - start)
