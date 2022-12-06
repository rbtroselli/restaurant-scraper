import os
from advisor_scraper import AdvisorScraper


# paths
path = os.getcwd()
user_data_path = path+'/user_data'
executable_path = path+'/chromedriver'
# for windows:
# executable_path = path+'/chromedriver.exe'

# search url
url = 'https://www.tripadvisor.it/Restaurants-g187849-Milan_Lombardy.html'

# instantiate scraper class
scraper = AdvisorScraper(user_data_path, executable_path)

# get perimeter, scrape reviews
scraper.perimeter_definition(url, min_total=50, min_per_rank=0)
scraper.scrape_entity_review()
