from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import os
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC





class AdvisorScraper():

    def __init__(
        self, 
        user_data_path,
        executable_path,
        perimeter_list=[],
        driver=None
        ):
        self.user_data_path = user_data_path
        self.executable_path = executable_path
        self.perimeter_list = perimeter_list
        self.instantiate_driver()
        return


    def instantiate_driver(self):
        """
        Define Chrome options, instantiate driver
        """
        # chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'user-data-dir={self.user_data_path}')
        chrome_options.add_argument(f'--profile-directory=Default')
        # driver istance
        self.driver = webdriver.Chrome(
            executable_path = self.executable_path,
            options = chrome_options
        )
        return

    def load_page(self, url):
        """
        Load page, add constant sleep to wait for page load
        """
        self.driver.get(url)
        time.sleep(1)
        return

    def clean_string(self, s):
        """
        Clean string from newlines and "|"
        """
        s = s.replace()
        return s
    
    def perimeter_to_file(self):
        with open('perimeter.txt','w') as p:
            for line in self.perimeter_list:
                p.write(line+'\n')
        return

    def perimeter_definition(self, search_url, min_total=1200, min_per_rank=30):
        """
        Cycle until perimeter reaches limit AND 
        there is a minimum amount per each rank
        """
        url = search_url
        count_per_rank={'1':0,'2':0,'3':0,'4':0,'5':0}
        
        while len(self.perimeter_list) < min_total \
            or [i<min_per_rank for i in count_per_rank.values()]:
            
            self.load_page(url)
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # find all restaurant boxes
            boxes = soup.find_all(class_="YHnoF Gi o")

            if boxes == []:
                print('AOOOOOOOOOOOOOOO AUMENTA ATTESA CARICAMENTO PAGINA')
                time.sleep(100000)
                break

            # iterate for all of the restaurants in the page
            for box in boxes:
                # get restaurant reviews number
                restaurant_reviews_number = box.find(class_='IiChw').text.replace('.','').split(' ')[0]
                # if less than n reviews, discard
                if int(restaurant_reviews_number)<60:
                    continue
                # get restaurant url, attaching site url
                restaurant_partial_url = box.find(href=True)['href']
                restaurant_url = 'https://www.tripadvisor.it' + restaurant_partial_url 
                # controllo, se già presente non inserisco
                if restaurant_url in self.perimeter_list:
                    continue
                # append restaurant url to restaurant list
                self.perimeter_list.append(restaurant_url)

                restaurant_rank = box.find(class_='UctUV d H0').attrs['aria-label'].split()[1].replace(',','.')
                count_per_rank[str(int(float(restaurant_rank)))]+=1

                print(restaurant_url)
                print(restaurant_reviews_number)
                print(restaurant_rank)
            
            
            print(count_per_rank)

            # get next page url
            next_page = soup.find(class_='nav next rndBtn ui_button primary taLnk')['href']
            # break if there is no next page
            if next_page==None:
                break  
            # assign next page url and wait
            url = 'https://www.tripadvisor.it' + next_page
            time.sleep(random.uniform(1,3))
        self.perimeter_to_file()

        print(count_per_rank)
        print([i for i in count_per_rank.values()])
        print([i<25 for i in count_per_rank.values()])
        print(len(self.perimeter_list) < self.limit)
        print(len(self.perimeter_list) < self.limit and [i<25 for i in count_per_rank.values()])

        return



# diminuire tutte le attese di 0.5
# passare i parametri solo quando usi la funzione giusta