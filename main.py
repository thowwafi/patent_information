from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import unicodedata
from utils import *


BASE_URL = "https://data.epo.org/expert-services/index.html"


def find_text(soup, text):
    text_string = soup.find('divtitle', class_='coGrey skiptranslate', text=re.compile(text)).findNext('p').text
    return unicodedata.normalize("NFKD", text_string)

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
    document = driver.find_element(By.CLASS_NAME, 'pDocument')
    doc_html = driver.page_source
    soup = BeautifulSoup(doc_html, 'html.parser')
    title = find_text(soup, 'Title (en)')
    abstract = find_text(soup, 'Abstract (en)')
    publication = find_text(soup, 'Publication')
    application = find_text(soup, 'Application')
    ipc_numbers = find_text(soup, 'IPC')
    datas = [
        {
            'title': title,
            'abstract': abstract,
            'publication': publication,
            'application': application,
            'ipc_numbers': ipc_numbers, 
        }
    ]
    next_button = soup.find('div', {'data-dojo-attach-point':"btNextDocument"})
    while 'buttonDisabled' not in next_button.get('class'):
        driver.find_element(By.CLASS_NAME, 'btNextDocument').click()
        sleep_time(2)
        document = driver.find_element(By.CLASS_NAME, 'pDocument')
        doc_html = driver.page_source
        soup = BeautifulSoup(doc_html, 'html.parser')
        title = find_text(soup, 'Title (en)')
        abstract = find_text(soup, 'Abstract')
        publication = find_text(soup, 'Publication')
        application = find_text(soup, 'Application')
        ipc_numbers = find_text(soup, 'IPC')
        data = {
            'title': title,
            'abstract': abstract,
            'publication': publication,
            'application': application,
            'ipc_numbers': ipc_numbers, 
        }
        datas.append(data)
    df = pd.DataFrame(datas)
    df.to_csv(f'{year}.csv', index=False)

if __name__ == '__main__':
    year = 2021
    main(year)