from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
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


def find_applicants_and_inventors(soup, data, key):
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(key))
    low_key = key.lower()
    ul = element.find_next_sibling('ul')
    if ul:
        for i in range(1, 11):    
            applicants = ul.find_all('li')
            if i < len(applicants) or i == len(applicants):
                index = i - 1
                li = applicants[index]
                data[f'{low_key}_{i}'] = li.p.find(text=True)
                data[f'{low_key}_address_{i}'] = unicodedata.normalize("NFKD", li.span.text)
            else:
                data[f'{low_key}_{i}'] = None
                data[f'{low_key}_address_{i}'] = None
    else:
        print("here2")
        data[f'{low_key}_1'] = element.find_next('p').span.text
        address = element.find_next('p').span.find_next('span')
        data[f'{low_key}_address_1'] = unicodedata.normalize("NFKD", address.text)

    return data


def get_patent_data(soup):
    application = find_text(soup, 'Application')
    application_date = application.split(" ")[-1]
    publication = find_text(soup, 'Publication')
    publication_number = re.sub("[\(\[].*?[\)\]]", "", publication)  # remove brackets
    data = {
        'publication_number': publication_number,
        'application_date': application_date,
        'title': find_text(soup, 'Title (en)'),
        'ipc_number_1': find_ipc_numbers(soup, 'IPC', 1),
        'ipc_number_2': find_ipc_numbers(soup, 'IPC', 2),
        'ipc_number_3': find_ipc_numbers(soup, 'IPC', 3),
        'abstract': find_text(soup, 'Abstract'),
    }
    data = find_applicants_and_inventors(soup, data, 'Applicant')
    data = find_applicants_and_inventors(soup, data, 'Inventor')
    print('data', data)
    return data


def main(year: int):
    driver = set_up_selenium()
    driver.get(BASE_URL)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "dijit_form_Button_0_label"))).click()
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

    document = driver.find_element(By.CLASS_NAME, 'pDocument')
    document_html = document.get_attribute('innerHTML')
    soup = BeautifulSoup(document_html, 'html.parser')
    
    patent = get_patent_data(soup)
    doc_html = driver.page_source
    soup = BeautifulSoup(doc_html, 'html.parser')
    documentCount = soup.find('span', {'data-dojo-attach-point':"documentCount"})
    documentCount = int(documentCount.text)

    for _ in range(documentCount):
        document = driver.find_element(By.CLASS_NAME, 'pDocument')
        doc_html = document.get_attribute('innerHTML')
        soup = BeautifulSoup(doc_html, 'html.parser')
        try:
            patent = get_patent_data(soup)
        except Exception:
            print(traceback.format_exc())
        patents.append(patent)
        df = pd.DataFrame(patents)
        df.to_excel(f'patents_{year}.xlsx', index=False)
        driver.find_element(By.CLASS_NAME, 'btNextDocument').click()
        sleep_time(2)

if __name__ == '__main__':
    year = 2021
    main(year)