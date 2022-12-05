import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import os
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from advisor_scraper import AdvisorScraper





# paths
path = os.getcwd()
user_data_path = path+'/user_data'
executable_path = path+'/chromedriver'

# search url
url = 'https://www.tripadvisor.it/Restaurants-g187849-Milan_Lombardy.html'


scraper = AdvisorScraper(user_data_path, executable_path)

perimeter_dictionary = scraper.perimeter_definition(url, min_total=50, min_per_rank=0)
scraper.scrape_entity_review(list(perimeter_dictionary.keys()))

