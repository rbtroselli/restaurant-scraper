import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AdvisorScraper():
    # month translation text-number
    months_dict = {
        'gennaio':'01',
        'febbraio':'02',
        'marzo':'03',
        'aprile':'04',
        'maggio':'05',
        'giugno':'06',
        'luglio':'07',
        'agosto':'08',
        'settembre':'09',
        'ottobre':'10',
        'novembre':'11',
        'dicembre':'12'
    }

    def __init__(self, user_data_path, executable_path, driver=None, perimeter_list=None):
        self.user_data_path = user_data_path
        self.executable_path = executable_path
        self._instantiate_driver()
        self.perimeter_list = perimeter_list
        return


    def _instantiate_driver(self):
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


    def _load_page_and_wait(self, url):
        """
        Load page, add constant sleep to wait for page load
        """
        self.driver.get(url)
        time.sleep(random.uniform(1.5,2.5))
        return
    

    def _get_soup(self, url):
        """
        Get soup from url
        """
        self._load_page_and_wait(url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup


    def _load_expand_and_get_soup(self, url):
        """
        Expand Più button when it appears, return soup got after expansion
        """
        self._load_page_and_wait(url)
        # wait for the load of the "Più" button, then click it this expands all the reviews' texts
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ulBlueLinks"))).click()
            time.sleep(1)
        except:
            print('No "Più" button')
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup
    

    def _perimeter_to_file(self, perimeter_dictionary, output_file):
        """
        Write url from perimeter to file
        """
        with open(output_file,'w') as p:
            for key, value in perimeter_dictionary.items():
                p.write(key + '|' + value + '\n')
        return
    

    def _scrape_restaurant(self, soup, restaurant_url, restaurant_id):
        """
        Get restaurant info from its soup, return a list with all of the info
        """
        # get info from restaurant html
        restaurant_name = soup.find(class_='HjBfq').text.replace('\n',' ').replace('\r',' ').replace('|','-')
        restaurant_rank = soup.find(class_='UctUV d H0').attrs['aria-label'].split()[1].replace(',','.')
        restaurant_address = soup.find_all(class_='AYHFM')[1].text.replace('\n',' ').replace('\r',' ').replace('|','-')
        restaurant_phone = soup.find_all(class_='AYHFM')[2].text.replace(' ','')
        restaurant_avg_price = soup.find(class_='dlMOJ').text
        print(restaurant_id, restaurant_name, restaurant_rank, 
            restaurant_address, restaurant_phone, restaurant_avg_price, restaurant_url)
        # fields in a list to return
        field_list = [restaurant_id, restaurant_name, restaurant_rank, 
            restaurant_address, restaurant_phone, restaurant_avg_price, restaurant_url]
        return field_list


    def _scrape_review(self, review_soup, restaurant_id):
        """
        Get review info from its soup, return a list with all of the info
        """
        # get info from review html
        review_partial_url = review_soup.find(href=True)['href']
        review_url = 'https://www.tripadvisor.it' + review_partial_url
        review_date_text = review_soup.find(class_='ratingDate')['title']
        review_date = '-'.join([self.months_dict.get(i, i) for i in reversed(review_date_text.split())])
        review_title = review_soup.find(class_='noQuotes').text.replace('\n',' ').replace('\r',' ').replace('|','-')
        review_text = review_soup.find(class_='partial_entry').text.replace('\n',' ').replace('\r',' ').replace('|','-')
        review_bubbles = review_soup.find(class_='ui_column is-9').find_all('span')[0]
        review_vote = review_bubbles.attrs['class'][1][-2:-1]
        review_user = review_soup.find(class_='info_text pointer_cursor').text
        print(restaurant_id, review_user, review_date, 
            review_vote, review_title, review_text, review_url)
        # fields in a list to return
        field_list = [restaurant_id, review_user, review_date, 
            review_vote, review_title, review_text, review_url]
        return field_list
    

    def _scrape_restaurant_box(self, box_soup):
        """
        Scrape restaurant box in search page, get and return info
        """
        restaurant_reviews_number = box_soup.find(class_='IiChw').text.replace('.','').split(' ')[0]
        restaurant_url = 'https://www.tripadvisor.it' + box_soup.find(href=True)['href']
        restaurant_rank = box_soup.find(class_='UctUV d H0').attrs['aria-label'].split()[1].replace(',','.')
        print(restaurant_reviews_number, restaurant_url, restaurant_rank)
        return restaurant_reviews_number, restaurant_url, restaurant_rank


    def _get_next_page(self, soup):
        """
        Get next page url, if no new button (last page), return False
        """
        try:
            url = 'https://www.tripadvisor.it' + soup.find(class_='nav next rndBtn ui_button primary taLnk')['href']
            return url
        except TypeError:
            print('No new button, pages finished.')
            return False
        

    def perimeter_definition(self, search_url, min_total=1000, min_per_rank=25, output_file='perimeter.txt'):
        """
        Cycle until perimeter reaches limit AND there is a minimum amount per each rank
        """
        perimeter_dictionary = {}
        count_per_rank = {'1.0':0, '1.5':0, '2.0':0, '2.5':0,
            '3.0':0, '3.5':0, '4.0':0, '4.5':0, '5.0':0}
        
        while (len(perimeter_dictionary) < min_total) or (True in [i<min_per_rank for i in count_per_rank.values()]):
            
            try:
                soup = self._get_soup(search_url)

                # find all restaurant boxes
                boxes = soup.find_all(class_="YHnoF Gi o")
                for box_soup in boxes:
                    try:
                        restaurant_reviews_number, restaurant_url, restaurant_rank = self._scrape_restaurant_box(box_soup)
                        # if less than n reviews discard, if cap reached discard
                        if int(restaurant_reviews_number) < 25: 
                            continue
                        if count_per_rank[restaurant_rank] >= 250:
                            continue
                        # add (no duplicates) to dictionary and increase count
                        perimeter_dictionary[restaurant_url] = restaurant_rank
                        count_per_rank[restaurant_rank]+=1
                    except Exception as e:
                        print(e, 'Box error, skipping...')
                        continue

                print(count_per_rank)
                # get next page, break while if last page
                search_url = self._get_next_page(soup)
                if search_url == False: 
                    break

            # if error in the page, get to next page, break while if last page
            except:
                search_url = self._get_next_page(soup)
                if search_url == False: 
                    break
                # if url is valid, skip page and go on
                print('Page error, skipping...')
                continue
        
        # write perimeter to file
        self._perimeter_to_file(perimeter_dictionary, output_file)
        self.perimeter_list = list(perimeter_dictionary.keys())
        return list(perimeter_dictionary.keys())


    def scrape_entity_review(self, restaurant_url_list=None):
        """
        Scrape restaurants and their reviews
        """
        if restaurant_url_list == None: restaurant_url_list = self.perimeter_list
        # write header on output files, and open in append mode
        with open('restaurant.csv','w') as restaurant_file:
            restaurant_file.write('restaurant_id|name|rank|address|phone|avg_price|url\n')
        with open('review.csv','w') as review_file:
            review_file.write('restaurant_id|user|date|vote|title|text|url\n')
        restaurant_file = open('restaurant.csv','a')
        review_file = open('review.csv','a')

        for restaurant_url in restaurant_url_list:
            try: 
                soup = self._get_soup(restaurant_url)
                restaurant_id = restaurant_url.split('-')[2]
                fields = self._scrape_restaurant(soup, restaurant_url, restaurant_id)
                restaurant_file.write('|'.join([s for s in fields])+'\n')
                
                # iterate reviews pages, 10 review per each
                for j in (0,10,20):
                    try:
                        restaurant_reviews_url = restaurant_url.replace('Reviews-',f'Reviews-or{j}-')
                        restaurant_soup = self._load_expand_and_get_soup(restaurant_reviews_url)
                        
                        # initialize an empty string to attach reviews and write only once, iterate reviews
                        review_lines = ''
                        reviews = restaurant_soup.find_all(class_='reviewSelector')
                        for review_soup in reviews:
                            try:
                                fields = self._scrape_review(review_soup, restaurant_id)
                                review_lines = review_lines + '|'.join([s for s in fields])+'\n'
                            except Exception as e:
                                print(e, 'Review error, skipping...')
                                continue
                        
                        # write review lines, flush file buffers and print review iteration
                        review_file.write(review_lines)
                        restaurant_file.flush()
                        review_file.flush()
                        print(j)

                    except Exception as e:
                        print(e, 'Review page error, skipping...')
                        continue
            except Exception as e:
                print(e, 'Restaurant page error, skipping...')
                continue
        
        restaurant_file.close()
        review_file.close()
        return

# capire dove mettere driver.close()
# parametrizzare hard cap e simili!!! Tipo i minimi
# check Più|
# check, se duplicati nel dizionario non incrementare relativo count del rank
