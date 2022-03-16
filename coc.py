from bs4 import BeautifulSoup as bs4
from datetime import timedelta
from fuzzywuzzy import process
from log_settings import logger
import numpy as np
import os
import pandas as pd
import re
from timeit import default_timer as timer
import urllib
from urllib.request import urlopen


home = os.getcwd()
outputs = os.path.join(home, 'new_output')

params = {
    "handelsnaam": "",
    "kvknummer": "",
    "straat": "",
    "postcode": "",
    "huisnummer": "",
    "plaats": "",
    "hoofdvestiging": "1",
    "rechtspersoon": "1",
    "nevenvestiging": "0",
    "zoekvervallen": "0",
    "zoekuitgeschreven": "1",
    "start": "0",
    "error": "false",
    "searchfield": "uitgebreidzoeken",
    "_": "1647354789433"
}

def make_request(params):
    parameters = urllib.parse.urlencode(params)
    url = f"https://zoeken.kvk.nl/search.ashx?{parameters}"
    print('url', url)
    uClient = urlopen(url, timeout=60)
    page_html = uClient.read()
    uClient.close()

    return page_html


def find_kvk_number(page_html, name):
    soup = bs4(page_html, 'html.parser')
    res_count = soup.find('strong')
    count = int(res_count.text) if res_count else 0
    print('count', count)
    if count == 1:
        kvk = soup.find('li', text=re.compile('KVK'))
        print('kvk', kvk.text)
        return kvk.text.replace("KVK ", "")
    elif count > 1:
        texts = [i.text for i in soup.find_all('h3', class_="handelsnaamHeader")]
        res = process.extract(name, texts)
        div = soup.find('h3', text=res[0][0])
        kvk = div.parent.parent.find('li', text=re.compile('KVK'))
        print('kvk', kvk.text)
        return kvk.text.replace("KVK ", "")
    else:
        return None


def get_coc(name, address, coc):
    if coc is not None and isinstance(coc, str):
        return coc
    if not address.endswith('NL'):
        return None
    print(name, address)
    params['plaats'] = address.split(" ")[-2]
    params['handelsnaam'] = name

    match_zipcode =  re.search(r"\b\d{4}\s?[A-Z]{2}\b", address, re.IGNORECASE)
    if match_zipcode:
        params['postcode'] = match_zipcode.group(0).replace(" ", "")
    match =  re.search(r"([a-zA-Z\.\'\/\- ]+) (\w{1,4})", address, re.IGNORECASE)
    if match:
        params['straat'] = match.group(1)
        params['huisnummer'] = match.group(2)

    page_html = make_request(params)

    kvk_number = find_kvk_number(page_html, name)
    if not kvk_number:
        params['plaats'] = ""
        params['straat'] = ""
        params['huisnummer'] = ""
        params['postcode'] = ""

        page_html = make_request(params)
        kvk_number = find_kvk_number(page_html, name)
        if not kvk_number:
            params["nevenvestiging"] = "1"
            params["rechtspersoon"] = "0"
            params["zoekvervallen"] = "1"

            page_html = make_request(params)
            kvk_number = find_kvk_number(page_html, name)
            if not kvk_number:
                logger.info(f"No result for {name} -- {address}")
                return None
            return kvk_number
        return kvk_number
    return kvk_number


def run(year_path):
    columns = ['applicant_name', 'applicant_address', 'COC']
    path = os.path.join(outputs, year_path)
    df = pd.read_excel(path, dtype=str)
    if 'COC' not in df.columns:
        df['COC'] = None
    df_unique = df.drop_duplicates(subset=['applicant_name', 'applicant_address'])[columns]
    count = 0
    for index, row in df_unique.iterrows():
        print(year_path, f"{count}/{len(df_unique)}")
        if not row['applicant_address'].endswith('NL'):
            continue
        coc_number = get_coc(row['applicant_name'], row['applicant_address'], row['COC'])
        if pd.isna(coc_number) or not coc_number:
            print(row['applicant_name'], row['applicant_address'])
            # coc_number = input("Enter KVK number: \t\n")
        df_unique.at[index, 'COC'] = coc_number
        query = (df['applicant_name'] == row['applicant_name']) & (df['applicant_address'] == row['applicant_address'])
        df.loc[query, 'COC'] = coc_number
        count += 1
    df.to_excel(path, index=False)
    return


if __name__ == '__main__':
    extensionsToCheck = ["2019", "2018", "2017", "2016", "2015"]
    for year_path in sorted(os.listdir(outputs), reverse=True):
        if any(ext in year_path for ext in extensionsToCheck):
            start = timer()
            run(year_path)
            end = timer()
            print(timedelta(seconds=end-start))
            logger.info(f"{year_path} -- done -- {timedelta(seconds=end-start)}")
    print('done')
    logger.info('done')
