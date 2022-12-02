from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import random
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

    def __init__(
        self, 
        user_data_path,
        executable_path,
        driver=None
        ):
        self.user_data_path = user_data_path
        self.executable_path = executable_path
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
    
    def perimeter_to_file(self, perimeter_dictionary, output_file):
        with open(output_file,'w') as p:
            for key, value in perimeter_dictionary.items():
                p.write(key + '|' + value + '\n')
        return

    def perimeter_definition(self, search_url, min_total=1000, min_per_rank=25, output_file='perimeter.txt'):
        """
        Cycle until perimeter reaches limit AND 
        there is a minimum amount per each rank
        """
        url = search_url
        perimeter_dictionary = {}
        count_per_rank = {'1':0,'2':0,'3':0,'4':0,'5':0}
        
        while (len(perimeter_dictionary) < min_total) or (True in [i<min_per_rank for i in count_per_rank.values()]):
            
            try:
                self.load_page(url)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # find all restaurant boxes
                boxes = soup.find_all(class_="YHnoF Gi o")

                # iterate for all of the restaurants in the page
                for box in boxes:
                    try:
                        # get restaurant reviews number
                        restaurant_reviews_number = box.find(class_='IiChw').text.replace('.','').split(' ')[0]
                        # if less than n reviews, discard
                        if int(restaurant_reviews_number) < 25:
                            continue
                        # get restaurant url, attaching site url
                        restaurant_url = 'https://www.tripadvisor.it' + box.find(href=True)['href']
                        restaurant_rank = box.find(class_='UctUV d H0').attrs['aria-label'].split()[1].replace(',','.')

                        # hard cap per each rank
                        if count_per_rank[str(int(float(restaurant_rank)))] >= 500:
                            continue

                        # dictionary doesn't support duplicates!
                        perimeter_dictionary[restaurant_url] = restaurant_rank
                        count_per_rank[str(int(float(restaurant_rank)))]+=1

                        print(restaurant_url)
                        print(restaurant_reviews_number)
                        print(restaurant_rank)
                    except:
                        print('Box error, skipping...')
                        continue
                
                print(count_per_rank)

                # get next page url
                next_page = soup.find(class_='nav next rndBtn ui_button primary taLnk')['href']
                # break if there is no next page
                if next_page==None:
                    break  
                # assign next page url and wait
                url = 'https://www.tripadvisor.it' + next_page
                time.sleep(random.uniform(1,3))
            except:
                # get next page url
                next_page = soup.find(class_='nav next rndBtn ui_button primary taLnk')['href']
                # break if there is no next page
                if next_page==None:
                    break  
                # assign next page url and wait
                url = 'https://www.tripadvisor.it' + next_page
                time.sleep(random.uniform(1,3))
                print('Page error, skipping...')
                continue
            
        self.perimeter_to_file(perimeter_dictionary, output_file)
        return perimeter_dictionary

    def scrape_entity_review(self, restaurant_url_list):

        # write header on output files
        with open('restaurant.csv','w') as restaurant_file:
            restaurant_file.write('id|name|rank|address|phone|avg_price|url\n')
        with open('review.csv','w') as review_file:
            review_file.write('restaurant_id|user|date|vote|title|text|url\n')

        # open in append mode output files
        restaurant_file = open('restaurant.csv','a')
        review_file = open('review.csv','a')

        for restaurant_url in restaurant_url_list:
            try: 
                # load page and wait
                self.load_page(restaurant_url)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                print(restaurant_url)
                
                # get details from inside restaurant page
                restaurant_id = restaurant_url.split('-')[2]
                print(restaurant_id)

                restaurant_name = soup.find(class_='HjBfq').text.replace('\n',' ').replace('\r',' ').replace('|','-')
                print(restaurant_name)

                restaurant_rank = soup.find(class_='UctUV d H0').attrs['aria-label'].split()[1].replace(',','.')
                print(restaurant_rank)
                
                restaurant_address = soup.find_all(class_='AYHFM')[1].text.replace('\n',' ').replace('\r',' ').replace('|','-')
                print(restaurant_address)
                
                restaurant_phone = soup.find_all(class_='AYHFM')[2].text.replace(' ','')
                print(restaurant_phone)

                restaurant_avg_price = soup.find(class_='dlMOJ').text
                print(restaurant_avg_price)

                # fields, write to file
                field_list = [
                    restaurant_id,
                    restaurant_name,
                    restaurant_rank,
                    restaurant_address,
                    restaurant_phone,
                    restaurant_avg_price,
                    restaurant_url
                ]
                line = '|'.join([s for s in field_list])+'\n'
                restaurant_file.write(line)
                
                time.sleep(random.uniform(0.5,1.5))
                
                j = 0
                for j in (0,10,20):

                    try:
                        restaurant_reviews_url = restaurant_url.replace('Reviews-',f'Reviews-or{j}-')
                        
                        # open reviews_page
                        self.load_page(restaurant_reviews_url)

                        # wait for the load of the "Più" button, then click it
                        # this expands all the reviews' texts
                        try:
                            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ulBlueLinks"))).click()
                            time.sleep(0.5)
                        except:
                            print('No "Più" button')

                        restaurant_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                        reviews = restaurant_soup.find_all(class_='reviewSelector')

                        # empty string to attach all the lines of the reviews
                        reviews_lines = ''
                        # iterate reviews
                        for review in reviews:
                            try:
                                # review fields
                                # region
                                review_partial_url = review.find(href=True)['href']
                                review_url = 'https://www.tripadvisor.it' + review_partial_url

                                review_date_text = review.find(class_='ratingDate')['title']
                                review_date = '-'.join([self.months_dict.get(i, i) for i in reversed(review_date_text.split())])

                                review_title = review.find(class_='noQuotes').text.replace('\n',' ').replace('\r',' ').replace('|','-')

                                review_text = review.find(class_='partial_entry').text.replace('\n',' ').replace('\r',' ').replace('|','-')

                                review_bubbles = review.find(class_='ui_column is-9').find_all('span')[0]
                                review_vote = review_bubbles.attrs['class'][1][-2:-1]

                                review_user = review.find(class_='info_text pointer_cursor').text
                                # endregion
                                
                                # prints
                                # region
                                print(review_url)
                                print(review_date)
                                print(review_title)
                                print(review_text)
                                print(review_vote)
                                print(review_user)
                                # endregion

                                # write to file
                                field_list = [
                                    restaurant_id,
                                    review_user,
                                    review_date,
                                    review_vote,
                                    review_title,
                                    review_text,
                                    review_url
                                ]
                                line = '|'.join([s for s in field_list])+'\n'
                                # append line to lines
                                reviews_lines = reviews_lines + line
                            except:
                                print('Review error, skipping...')
                                continue
                        
                        # write lines to file, flush
                        review_file.write(reviews_lines)
                        restaurant_file.flush()
                        review_file.flush()

                        # print review iteration and sleep
                        print(j)
                        time.sleep(random.uniform(0.5,1.5))
                            
                    except:
                        print('Review page error, skipping...')
                        continue
            except:
                print('Restaurant page error, skipping...')
                continue
        restaurant_file.close()
        review_file.close()
        return

# diminuire tutte le attese di 0.5
# passare i parametri solo quando usi la funzione giusta
# rimuovere funzioni per cui non serve lo status dall'oggetto, tipo quelle che lavorano la stringa o next_page
# capire dove mettere i driver.close()
# sistemare i print
# parametrizzare hard cap e simili!!! Tipo i minimi