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
    driver = set_up_selenium(browser='chrome')

    patentCitations = []
    non_patent_citations = []
    data_cited_by = []

    for index, number in enumerate(publication_numbers):
        print(f"{index}/{len(publication_numbers)}", year_path)
        print('number', number)
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

        if not soup.find('h3', id='patentCitations'):
            citation = {
                "publication_number": number,
                "patent_citation": 0,
                "publication_date": 0,
                "assignee": 0,
                "title": 0
            }
            patentCitations.append(citation)
        else:
            citations = get_data_tables(soup, number, 'patentCitations')
            patentCitations.extend(iter(citations))

        if not soup.find('h3', id='citedBy'):
            citation = {
                "publication_number": number,
                "patent_citation": 0,
                "publication_date": 0,
                "assignee": 0,
                "title": 0
            }
            data_cited_by.append(citation)
        else:
            citedBy_s = get_data_tables(soup, number, 'citedBy')
            data_cited_by.extend(iter(citedBy_s))

        if not soup.find('h3', id='nplCitations'):
            citation = {
                "publication_number": number,
                "patent_citation": 0,
                "publication_date": 0,
                "assignee": 0,
                "title": 0
            }
            non_patent_citations.append(citation)
        else:
            h3_pc = soup.find('h3', id='nplCitations')
            pc_table = h3_pc.find_next('div', class_='responsive-table')
            for tr in pc_table.find_all('div', class_='tr')[1:]:
                citation = {
                    "publication_number": number,
                    "patent_citation": 0,
                    "publication_date": 0,
                    "assignee": 0,
                    "title": tr.text.replace('*', '').strip()
                }
                non_patent_citations.append(citation)
        sleep_time(1)

    output_name = year_path.replace(".xlsx", "")
    output_file = os.path.join(output_citations, f"{output_name}_citations.xlsx")

    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    pd.DataFrame(patentCitations).to_excel(writer, sheet_name='PatentCitations', index=False)
    pd.DataFrame(non_patent_citations).to_excel(writer, sheet_name='NonPatentCitations', index=False)
    pd.DataFrame(data_cited_by).to_excel(writer, sheet_name='CitedBy', index=False)
    writer.save()
    writer.close()

    driver.quit()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Please specify year from and year to')
        sys.exit()
    from_year = int(sys.argv[1])
    to_year = int(sys.argv[2])
    extensionsToCheck = [str(i) for i in list(range(from_year, to_year))]
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
