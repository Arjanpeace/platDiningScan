# System Packages
from platDining.functions import *
import time

if __name__ == "__main__":
    #
    # file_path = sys.argv[0]
    # base variables
    start = time.time()
    main_url = "https://dining-offers-prod.amex.r53.tuimedia.com/api/countries"
    country_url = 'https://dining-offers-prod.amex.r53.tuimedia.com/api/country/{0}/merchants'

    # Get all countries
    countries = getCountries(main_url)

    # Get all different merchants
    countryList = countries['key'].unique()
    merchants = getMerchants(country_url, countryList)
    data = merchantGroupDivider(merchants)

    # Make full dataset
    data = pd.merge(data,
                    countries,
                    left_on='country',
                    right_on='key',
                    how='left')

    # Try to determine coordinates
    data['coordinates'] = data.apply(lambda x: coordinates(x), axis=1)

    # Output the file
    data.to_csv('output/map.csv', index=False)
    
    print(time.time() - start)



