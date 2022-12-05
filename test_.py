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

# aggiungere opzione per rifare scraping perimeter o meno
#   se off, prendo il perimetro dal file e skippo quella parte
# aggiungere tutte le opzioni in un file di configurazione



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

# paths
path = os.getcwd()
user_data_path = path+'/user_data'
executable_path = path+'/chromedriver'

# chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f'user-data-dir={user_data_path}')
chrome_options.add_argument(f'--profile-directory=Default')

# search url
url = 'https://www.tripadvisor.it/Restaurants-g187849-Milan_Lombardy.html'

restaurants_goal_number = 1200


# istantiate driver
driver = webdriver.Chrome(
    executable_path=executable_path,
    options=chrome_options
)




# parameterize file names!!!



# load page and wait
driver.get(url)
time.sleep(1)


# list containing all of the restaurants urls
restaurant_url_list = []

# iterate until 1500 restaurants are collected
while len(restaurant_url_list)<restaurants_goal_number:

    # get html from page
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # find all restaurant boxes
    boxes = soup.find_all(class_="YHnoF Gi o")

    # iterate for all of the restaurants in the page
    for box in boxes:
        # get restaurant reviews number
        restaurant_reviews_number = box.find(class_='IiChw').text.replace('.','').split(' ')[0]
        print('reviews number: ' + restaurant_reviews_number)
        # if less than 50 reviews, discard
        if int(restaurant_reviews_number)<70:
            continue
        
        # get restaurant url, attaching site url
        restaurant_partial_url = box.find(href=True)['href']
        restaurant_url = 'https://www.tripadvisor.it' + restaurant_partial_url 
        print(restaurant_url)


        # controllo su sponsor, se true continue

        # controllo, se già presente non inserisco
        if restaurant_url in restaurant_url_list:
            continue

        # append restaurant url to restaurant list
        restaurant_url_list.append(restaurant_url)

    # get next page url
    next_page = soup.find(class_='nav next rndBtn ui_button primary taLnk')['href']

    # break if there is no next page
    if next_page==None:
        break
    
    # go to next page and wait
    driver.get('https://www.tripadvisor.it' + next_page)
    time.sleep(random.uniform(1,3))


# print restaurant list
print(restaurant_url_list)
print(len(restaurant_url_list))


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
        driver.get(restaurant_url)
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

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

        # prendere vari dettagli extra (tipo subvoti)


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
        
        time.sleep(random.uniform(1,2))
        
        j = 0
        for j in (0,10,20,30,40,50):

            try:
                restaurant_reviews_url = restaurant_url.replace('Reviews-',f'Reviews-or{j}-')
                
                # open reviews_page
                driver.get(restaurant_reviews_url)
                time.sleep(1)

                # wait for the load of the "Più" button, then click it
                # this expands all the reviews' texts
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ulBlueLinks"))).click()
                    time.sleep(0.5)
                except:
                    print('######## NO BUTTON?!')
                    continue

                html = driver.page_source
                restaurant_soup = BeautifulSoup(html, 'html.parser')

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
                        review_date = '-'.join([months_dict.get(i, i) for i in reversed(review_date_text.split())])

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
                        continue
                
                # write lines to file, flush
                review_file.write(reviews_lines)
                restaurant_file.flush()
                review_file.flush()

                # print review iteration and sleep
                print(j)
                time.sleep(random.uniform(1,2))
                    
            except:
                continue
    except:
        continue








    # apro e prendo cose. poi prendo review con un for, rimpiazzo pezzo di link fino a che non arrivo a 50 review



    
    

restaurant_file.close()
review_file.close()

driver.close()



