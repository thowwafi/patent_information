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
    try:
        text_string = element.find_next('p').text
    except AttributeError as err:
        if text == 'Abstract':
            return None
        with open('log.txt', 'a') as f:
            f.write(str(traceback.format_exc()))
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
    publication_date = publication.split(" ")[-1]
    data = {}
    data = find_applicants_and_inventors(soup, data, 'Applicant')
    data['title'] = find_text(soup, 'Title (en)')
    data['abstract'] = find_text(soup, 'Abstract')
    data['publication_number'] = publication_number
    data['publication_date'] = publication_date
    data['application_number'] = application
    data['application_date'] = application_date
    data['ipc_number_1'] = find_ipc_numbers(soup, 'IPC', 1)
    data['ipc_number_2'] = find_ipc_numbers(soup, 'IPC', 2)
    data['ipc_number_3'] = find_ipc_numbers(soup, 'IPC', 3)
    data = find_applicants_and_inventors(soup, data, 'Inventor')
    print('data', data)
    return data

class text_to_change(object):
    
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        actual_text = driver.find_element(*self.locator).text
        return actual_text != self.text


def main(year: int):
    driver = set_up_selenium()
    driver.get(BASE_URL)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "dijit_form_Button_0_label"))).click()
    sleep_time(2)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'dijit__WidgetsInTemplateMixin_1'))).click()
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

    doc_html = driver.page_source
    soup = BeautifulSoup(doc_html, 'html.parser')
    documentCount = soup.find('span', {'data-dojo-attach-point':"documentCount"})
    count = unicodedata.normalize("NFKD", documentCount.text)
    documentCount = int(count.replace(" ", ""))

    text_before = ''
    for _ in range(documentCount):
        print('text_before', text_before)
        WebDriverWait(driver, 10).until(
            text_to_change((By.CLASS_NAME, "titleContainer"), text_before)
        )
        document = driver.find_element(By.CLASS_NAME, 'pDocument')
        doc_html = document.get_attribute('innerHTML')
        soup = BeautifulSoup(doc_html, 'html.parser')
        try:
            patent = get_patent_data(soup)
        except Exception:
            print(traceback.format_exc())
            with open('log.txt', 'a') as f:
                f.write(str(traceback.format_exc()))
            continue
        patents.append(patent)
        df = pd.DataFrame(patents)
        df.to_excel(f'patents_{year}.xlsx', index=False)
        text_before = driver.find_element(By.CLASS_NAME, 'titleContainer').text
        driver.find_element(By.CLASS_NAME, 'btNextDocument').click()


if __name__ == '__main__':
    year = 2021
    main(year)


# https://data.epo.org/pise-server/rest/databases/EPAB2022001/documents/EP3741204A120201125?section=BIBLIOGRAPHIC_DATA&sectionType=TEXTUAL&searchId=31277645-9ebd-41fc-82f6-e371062b45a7&field=TIEN&field=TIDE&field=TIFR&field=ABEN&field=ABDE&field=ABFR&field=EP_&field=APN_DOC&field=PRN_DOC&field=PAAP&field=DIAP&field=DCS&field=DXS&field=DVS&field=IC17&field=ICF&field=CPC&field=CSET&field=APP_WORD&field=INV_WORD&field=REP_WORD&field=IPUN_DOC&field=IAPN_DOC&field=CPAP_DOC&field=CNAP_DOC&field=CPEP&field=CNEP&field=COD&field=PUA12&field=PUA3&field=PUB1&field=PUB2&field=PUB3&field=ISFAM&field=IFAM&field=CLEN&field=CLDE&field=CLFR&format=HTML&request.preventCache=1641457001517