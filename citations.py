import enum
from bs4 import BeautifulSoup
from datetime import timedelta
from log_settings import logger
import os
import openpyxl
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import sys
import time
from timeit import default_timer as timer
from utils import set_up_selenium, sleep_time


home = os.getcwd()
outputs = os.path.join(home, 'output_excel')
output_citations = os.path.join(home, 'output_citations')


def get_data_tables(soup, number, div_id):
    h3_pc = soup.find('h3', id=div_id)
    pc_table = h3_pc.find_next('div', class_='responsive-table')
    data = []
    for tr in pc_table.find_all('div', class_='tr'):
        if tr.text.strip().startswith("Publication") or tr.text.strip().startswith("Family"):
            continue
        patent_citation = tr.find_all("span", class_="td")[0].text.replace("*", "").strip()
        publication_date = tr.find_all("span", class_="td")[2].text.strip()
        assignee = tr.find_all("span", class_="td")[3].text.strip()
        title = tr.find_all("span", class_="td")[4].text.strip()
        citation = {
            "publication_number": number,
            "patent_citation": patent_citation,
            "publication_date": publication_date,
            "assignee": assignee,
            "title": title
        }
        data.append(citation)
    return data


def get_citations(year_path):
    """
    Returns a list of citations in the given file.
    """
    path = os.path.join(outputs, year_path)
    df = pd.read_excel(path, dtype=str)
    publication_numbers = df.publication_number.str.split(' ').str[:3].str.join('')
    publication_numbers = publication_numbers.drop_duplicates()
    driver = set_up_selenium(browser='firefox')

    patentCitations = []
    cited_bys = []
    for index, number in enumerate(publication_numbers):
        print(f"{index}/{len(publication_numbers)}")
        print('number', number)
        if index > 10:
            continue    # only get the first 10
        url = f"https://patents.google.com/patent/{number}/en?oq={number}"
        driver.get(url)
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "footer"))
            )
        except TimeoutException:
            print('Loading took too much time!')
            continue

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "patentCitations"))
            )
        except TimeoutException:
            citation = {
                "publication_number": number,
                "patent_citation": 0,
                "publication_date": 0,
                "assignee": 0,
                "title": 0
            }
            patentCitations.append(citation)

        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "citedBy"))
            )
        except TimeoutException:
            citation = {
                "publication_number": number,
                "patent_citation": 0,
                "publication_date": 0,
                "assignee": 0,
                "title": 0
            }
            cited_bys.append(citation)
            continue

        citations = get_data_tables(soup, number, 'patentCitations')
        patentCitations.extend(iter(citations))
        citedBy_s = get_data_tables(soup, number, 'citedBy')
        cited_bys.extend(iter(citedBy_s))
    output_name = year_path.replace(".xlsx", "")
    output_file = os.path.join(output_citations, f"{output_name}_citations.xlsx")
    pd.DataFrame(patentCitations).to_excel(output_file, sheet_name="PatentCitations", index=False)
    writer = pd.ExcelWriter(output_file, engine='openpyxl')

    if os.path.exists(output_file):
        book = openpyxl.load_workbook(output_file)
        writer.book = book
    df_citedby = pd.DataFrame(cited_bys)
    df_citedby.to_excel(writer, sheet_name='CitedBy')
    writer.save()
    writer.close()

    driver.quit()


if __name__ == '__main__':
    extensionsToCheck = [str(i) for i in list(range(2021, 2022))]
    for year_path in sorted(os.listdir(outputs), reverse=True):
        if any(ext in year_path for ext in extensionsToCheck):
            print(year_path)
            start = timer()
            get_citations(year_path)
            end = timer()
            print(timedelta(seconds=end-start))
            logger.info(f"{year_path} -- done -- {timedelta(seconds=end-start)}")
    print('done')
    logger.info('done')