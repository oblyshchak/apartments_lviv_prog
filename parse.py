import csv
import logging

import numpy as np

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
CSV_PATH = 'may_riel.csv'
CSV_COLUMNS = [
    'district',
    'wall_material',
    'status',
    'balcony',
    'area_kitchen',
    'area_living',
    'area',
    'room',
    'floor',
    'superficiality',
    'type_build',
    'price'
]
URL = 'https://www.real-estate.lviv.ua/%D0%BE%D1%80%D0%B5%D0%BD%D0%B4%D0%B0-%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80/%D0%BC%D1%96%D1%81%D1%82%D0%BE-%D0%BB%D1%8C%D0%B2%D1%96%D0%B2/%D0%B4%D0%BD%D1%96%D0%B2-14'
EXCHANGE_DOLLAR = 38

data_objects = []
print(data_objects)
driver = webdriver.Chrome(options=chrome_options)


class Xpath:
    list_apartments = "//*[@id=\"search_result\"]/div[5]/div[*]/div[2]/a"
    list_description = "/html/body/div[2]/div[1]/ul"
    address = "/html/body/div[2]/div[1]/div[2]/div[1]/h3"
    next_page = "//*[@id=\"search_result\"]/ul[2]/li[@class = 'next page-item']/a"


def parse_element(url):
    while True:
        driver.get(url)
        logging.info(f"url: {url}")
        
        try:
            page = driver.find_element(By.XPATH, Xpath.next_page)
        except NoSuchElementException:
            logging.warning("next page is not found, reached the end of appartments list")
            break
    
        next_page_url = page.get_attribute('href')
        logging.info(f"got next page {next_page_url}")
        
        try:
            appartments_hrefs = driver.find_elements(By.XPATH, Xpath.list_apartments)
        except NoSuchElementException:
            logging.warning("can't find list of hrefs for appartments")
            continue
        
        parse_appartments(appartments_hrefs)
        
        # Set url to be next_page_url and continue the loop
        url = next_page_url

def parse_appartments(elements):
    hrefs = []
    for element in elements:
        # collect all objects from the web list
        href = element.get_attribute('href')
        hrefs.append(href)
    logging.info(f"get all hrefs: {hrefs}")

    for href in hrefs:
        # open each object in a new page and starting collect all info
        logging.info(f"Parsing: {href}")
        
        # Re-creating the webdriver due to an issue observed after an hour of parsing that leads to webdriver crash.
        # This is possibly a selenium webdriver issue and the only workaround I found is to re-create webdriver.
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(href)
        try:
            appartment_info = driver.find_element(By.XPATH, Xpath.list_description)
            address = driver.find_element(By.XPATH, Xpath.address)
            parse_appartment_info(appartment_info.text, address.text)
        except NoSuchElementException:
            pass
        
    
def parse_appartment_info(info, address):
    info = info.split('\n')
    price = parse_price(info)
    status = parse_str_values(info, 'Стан')
    building_type = parse_str_values(info, 'Тип будівлі')
    wall_material = parse_str_values(info, 'Матеріал стін')
    superficiality = parse_int_values(info, 'Поверховість')
    floor = parse_int_values(info, 'Поверх')
    rooms_num = parse_int_values(info, 'Кімнат')
    area = parse_int_values(info, 'Загальна площа')
    area_living = parse_int_values(info, 'Житлова площа')
    area_kitchen = parse_int_values(info, 'Площа кухні')
    balcony_num = parse_int_values(info, 'Балконів')
    district  = parse_address(address)

    full_info = [
            district,
            wall_material,
            status,
            balcony_num,
            area_kitchen,
            area_living,
            area,
            rooms_num,
            floor,
            superficiality,
            building_type,
            price
    ]
    
    data_objects.append(full_info)
    
    
#processing of received information
def parse_price(info):
    # Parse string like this: "Ціна: 7 900 грн" or "500 $ /міс"
    price = np.nan
    for element in info:
        if "Ціна" in element:
            price = [i for i in element if i.isdigit()]
            if 'грн' in element:
                if price:
                    price = int("".join(price).replace(" ", "").replace(".", ""))
                else:
                    price =  np.nan
                break
            else:
                if price:
                    price = int("".join(price).replace(" ", ""))
                    price = price * EXCHANGE_DOLLAR
                else:
                    price =  np.nan
                break
        
    return price


def parse_str_values(info, code_word):
    # Parse string like this: "Стан: відмінний" or "Тип будівлі: Будівля старого Львова"
    value = np.nan
    for element in info:
        if code_word in element:
            value = element.split(':')[-1]
            break
    
    return value


def parse_int_values(info, code_word):
    # Parse string like this: "Загальна площа: 45 кв.м" or "Кімнат: 1"
    value = np.nan
    for element in info:
        if code_word in element:
            value = [i for i in element if i.isdigit()]
            if value:
                value = int("".join(value).replace(" ", "").replace(".", ""))
                break
            else:
                value = np.nan
    return value


def parse_address(info):
    # Parse string like this: 'Трускавецька вул. Львів, Франківський район'"
    district = np.nan
    if 'район' in info:
        district = info.split(" ")[1]
    
    return district


#write csv file
def write_csv(data):
    with open(CSV_PATH, 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        
        writer.writerow(CSV_COLUMNS)
        for row in data:
            writer.writerow(row)
            

def main():
    logging.basicConfig(level=logging.INFO, filename='parser_riel.log', format='parser %(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"get page {URL}")
    parse_element(URL)
    write_csv(data_objects)
    

if __name__ == '__main__':
    main()
    
    
