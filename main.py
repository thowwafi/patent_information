from bs4 import BeautifulSoup
import pandas as pd
from pyexcelerate import Workbook
import re
from pandas.core.accessor import DirNamesMixin
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys
import traceback
import unicodedata
from utils import *
import logging


logger = logging.getLogger()
handler = logging.FileHandler('logfile.log')
logger.addHandler(handler)


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


def find_inventors(soup, data):
    key = 'Inventor'
    low_key = key.lower()
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(key))
    if not element:
        return data
    ul = element.find_next_sibling('ul')
    if ul:
        for i in range(1, 11):    
            applicants = ul.find_all('li')
            if i < len(applicants) or i == len(applicants):
                index = i - 1
                li = applicants[index]
                name = li.p.find(text=True)
                if name == 'The other inventor has waived his right to be thus mentioned.':
                    data[f'{low_key}_last_name_{i}'] = None
                    data[f'{low_key}_first_name_{i}'] = None
                else:
                    data[f'{low_key}_last_name_{i}'] = name.split(',')[0]
                    data[f'{low_key}_first_name_{i}'] = " ".join(name.split(',')[1:]).strip()
                address = li.span
                data[f'{low_key}_address_{i}'] = unicodedata.normalize("NFKD", address.text) if address else None
            else:
                data[f'{low_key}_last_name_{i}'] = None
                data[f'{low_key}_first_name_{i}'] = None
                data[f'{low_key}_address_{i}'] = None
    else:
        name = element.find_next('p').span.text
        if name == "The designation of the inventor has not yet been filed":
            data[f'{low_key}_last_name_1'] = None
            data[f'{low_key}_first_name_1'] = None
            data[f'{low_key}_address_1'] = None
        else:
            data[f'{low_key}_last_name_1'] = name.split(',')[0]
            data[f'{low_key}_first_name_1'] = " ".join(name.split(',')[1:]).strip()
            address = element.find_next('p').span.find_next('span')
            data[f'{low_key}_address_1'] = unicodedata.normalize("NFKD", address.text) if address else None
    return data


def find_applicants(soup, data):
    key = 'Applicant'
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
        data[f'{low_key}_1'] = element.find_next('p').span.text
        address = element.find_next('p').span.find_next('span')
        data[f'{low_key}_address_1'] = unicodedata.normalize("NFKD", address.text)

    return data


def find_ipc_numbers(soup, data):
    key = 'IPC'
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(key))
    low_key = key.lower()
    numbers = element.find_next('p').find_all('a', class_='text-nowrap')
    if not numbers:
        logger.error('IPC numbers not found')
        logger.error(str(data))
    for i, number in enumerate(numbers, start=1):
        data[f'{low_key}_number_{i}'] = unicodedata.normalize("NFKD", number.text)
    return data


def find_ipc_numbers_list(soup):
    key = 'IPC'
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(key))
    if not element:
        print('IPC numbers not found')
        return []
    numbers = element.find_next('p').find_all('a', class_='text-nowrap')
    return [unicodedata.normalize("NFKD", number.text) for number in numbers]


def find_applicants_list(soup):
    key = 'Applicant'
    element = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(key))
    ul = element.find_next_sibling('ul')
    datas = []
    if ul:
        for li in ul.find_all('li'):
            datas.append(
                {
                    'name': li.p.find(text=True),
                    'address': unicodedata.normalize("NFKD", li.span.text)
                }
            )
    else:
        address = element.find_next('p').span.find_next('span')
        datas.append(
            {
                'name': element.find_next('p').span.text,
                'address': unicodedata.normalize("NFKD", address.text)
            }
        )
    return datas


def get_patent_datas(soup):
    datas = []
    ipc_numbers = find_ipc_numbers_list(soup)
    applicants = find_applicants_list(soup)
    application = find_text(soup, 'Application')
    app_type, app_number, app_date = application.split(' ')
    
    publication = find_text(soup, 'Publication')
    publication_number = re.sub("[\(\[].*?[\)\]]", "", publication).strip()  # remove brackets
    publication_date = publication_number.strip().split(" ")[-1]
    print('publication_number', publication_number)

    title = find_text(soup, 'Title (en)')
    abstract = find_text(soup, 'Abstract')

    inventors = find_inventors(soup, {})
    for applicant in applicants:
        address = applicant['address']
        country_code = address.split(' ')[-1].strip()
        for ipc in ipc_numbers:
            data = {
                'applicant_name': applicant.get('name'),
                'applicant_address': address,
                'country_code': country_code,
                'application_type': app_type,
                'application_number': app_number,
                'application_date': app_date,
                'publication_number': publication_number,
                'publication_date': publication_date,
                'ipc_main': ipc_numbers[0],
                'ipc_number': ipc,
                'title': title,
                'abstract': abstract,
            }
            data.update(inventors)
            datas.append(data)
    return datas


def get_patent_data(soup):
    application = find_text(soup, 'Application')
    application_date = application.split(" ")[-1]
    publication = find_text(soup, 'Publication')
    publication_number = re.sub("[\(\[].*?[\)\]]", "", publication).strip()  # remove brackets
    publication_date = publication_number.strip().split(" ")[-1]
    title = find_text(soup, 'Title (en)')
    abstract = find_text(soup, 'Abstract')
    publication_number = publication_number
    publication_date = publication_date
    application_number = application
    application_date = application_date
    data = {}
    data = find_applicants(soup, data)
    data = find_ipc_numbers(soup, data)
    data = find_inventors(soup, data)
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
    driver = set_up_selenium(browser='firefox')
    driver.get(BASE_URL)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "dijit_form_Button_0_label"))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'dijit__WidgetsInTemplateMixin_1'))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'CodeMirror'))).click()
    actions = ActionChains(driver)
    actions.send_keys(f'APPCO = NL AND APD > {year} AND APD < {year + 1}')
    actions.perform()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'queryBlockContent_btLaunchQuery'))).click()
    sleep_time(2)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'goToResultLink'))).click()
    sleep_time(2)
    doc_html = driver.page_source
    soup = BeautifulSoup(doc_html, 'html.parser')
    documentCount = soup.find('span', {'data-dojo-attach-point':"documentCount"})
    count = unicodedata.normalize("NFKD", documentCount.text)
    documentCount = int(count.replace(" ", ""))

    df = pd.read_excel(f'patents_{year}.xlsx')
    # patents = ast.literal_eval(df.to_json(orient='records'))
    if documentCount == len(df):
        print('No new patents')
        driver.quit()
        return

    print('len(df)', len(df))
    if len(df) != 0:
        current_index = 1
        while current_index <= len(df):
            print(f'{current_index}/{len(df)}', end='\r')
            driver.find_element(By.CLASS_NAME, 'btNextDocument').click()
            current_index = driver.find_element(By.XPATH, '//span[@data-dojo-attach-point="documentIndex"]').text
            current_index = int(current_index.replace(" ", ""))
        documentCount -= len(df)
    patents = []
    text_before = ''
    for iter in range(documentCount):
        print('text_before', text_before)
        print('iter', f'{iter}/{documentCount}')
        WebDriverWait(driver, 2).until(
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
        newdf = pd.DataFrame(patents)
        df_res = pd.concat([df, newdf], ignore_index=True)
        values = [df_res.columns] + list(df_res.values)
        wb = Workbook()
        wb.new_sheet('Sheet1', data=values)
        wb.save(f'patents_{year}.xlsx')
        # df_res.to_excel(f'patents_{year}.xlsx', index=False)
        text_before = driver.find_element(By.CLASS_NAME, 'titleContainer').text
        driver.find_element(By.CLASS_NAME, 'btNextDocument').click()
    driver.quit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please specify year')
        sys.exit()
    year = int(sys.argv[1])
    try:
        main(year)
    except TimeoutException as e:
        print('e', e)
        main(year)
