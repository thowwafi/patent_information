from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import unicodedata
from utils import *


BASE_URL = "https://data.epo.org/expert-services/index.html"


def find_text(soup, text):
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=text)
    if not element:
        element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(text))
    text_string = element.find_next('p').text
    return unicodedata.normalize("NFKD", text_string)


def find_ipc_numbers(soup, text, index):
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=text)
    if not element:
        element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(text))
    numbers = element.find_next('p').find_all('span', class_='text-nowrap')
    if index < len(numbers) or index == len(numbers):
        loop = index - 1
        print('----')
        print(index)
        print(loop)
        print(len(numbers))
        return unicodedata.normalize("NFKD", numbers[loop].text)


def get_patent_data(driver):
    document = driver.find_element(By.CLASS_NAME, 'pDocument')
    doc_html = document.get_attribute('innerHTML')
    soup = BeautifulSoup(doc_html, 'html.parser')
    data = {
        'title': find_text(soup, 'Title (en)'),
        'abstract': find_text(soup, 'Abstract'),
        'publication': find_text(soup, 'Publication'),
        'application': find_text(soup, 'Application'),
        'ipc_number_1': find_ipc_numbers(soup, 'IPC', 1),
        'ipc_number_2': find_ipc_numbers(soup, 'IPC', 2),
        'ipc_number_3': find_ipc_numbers(soup, 'IPC', 3),
        'applicant_1': '',
        'address_1': '',
        'applicant_2': '',
        'address_2': '',
        'applicant_3': '',
        'address_3': '',
        'applicant_4': '',
        'address_4': '',
        'applicant_5': '',
        'address_5': '',
        'applicant_6': '',
        'address_6': '',
        'applicant_7': '',
        'address_7': '',
        'applicant_8': '',
        'address_8': '',
        'applicant_9': '',
        'address_9': '',
        'applicant_10': '',
        'address_10': '',
    }
    return data


def main(year: int):
    driver = set_up_selenium()
    driver.get(BASE_URL)
    sleep_time(10)
    driver.find_element(By.ID, 'dijit_form_Button_0_label').click()
    sleep_time(2)
    driver.find_element(By.ID, 'dijit__WidgetsInTemplateMixin_1').click()
    sleep_time(2)
    driver.find_elements(By.CLASS_NAME, 'CodeMirror')[0].click()
    actions = ActionChains(driver)
    actions.send_keys(f'APPCO = NL AND APD > {year} AND APD < {year + 1}')
    actions.perform()
    sleep_time(2)
    driver.find_element(By.ID, 'queryBlockContent_btLaunchQuery').click()
    sleep_time(2)
    driver.find_element(By.ID, 'goToResultLink').click()
    sleep_time(2)
    sleep_time(2)
    patents = []
    patent = get_patent_data(driver)
    doc_html = driver.page_source
    soup = BeautifulSoup(doc_html, 'html.parser')
    next_button = soup.find('div', {'data-dojo-attach-point':"btNextDocument"})
    while 'buttonDisabled' not in next_button.get('class'):
        driver.find_element(By.CLASS_NAME, 'btNextDocument').click()
        sleep_time(2)
        patent = get_patent_data(driver)
        patents.append(patent)
    df = pd.DataFrame(patents)
    df.to_csv(f'{year}.csv', index=False)

if __name__ == '__main__':
    year = 2021
    main(year)