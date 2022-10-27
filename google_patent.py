import enum
from bs4 import BeautifulSoup
from datetime import timedelta
from log_settings import logger
import os
import openpyxl
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
import sys
import time
from timeit import default_timer as timer
from utils import set_up_selenium, sleep_time


home = os.getcwd()
outputs = os.path.join(home, 'output_excel')
output_citations = os.path.join(home, 'output_citations')
citation_csv = os.path.join(home, 'citation_csv')


def get_data_tables(soup, number, div_id):
    h3_pc = soup.find('h3', id=div_id)
    pc_table = h3_pc.find_next('div', class_='responsive-table')
    data = []
    for tr in pc_table.find_all('div', class_='tr'):
        if tr.text.strip().startswith("Publication") or tr.text.strip().startswith("Family"):
            continue
        citation_number = tr.find_all("span", class_="td")[0].text.replace(" ", "").replace("\n", "")
        cited_by = ""
        if "*" in citation_number:
            cited_by = "examiner"
        elif "†" in citation_number:
            cited_by = "third_party"
        elif "‡" in citation_number:
            cited_by = "family_to_family"
        patent_citation = citation_number.strip()
        publication_date = tr.find_all("span", class_="td")[2].text.strip()
        assignee = tr.find_all("span", class_="td")[3].text.strip()
        title = tr.find_all("span", class_="td")[4].text.strip()
        citation = {
            "publication_number": number,
            "patent_citation": patent_citation,
            "publication_date": publication_date,
            "assignee": assignee,
            "title": title,
            "cited_by": cited_by
        }
        data.append(citation)
    return data


def get_citations(df):
    """
    Returns a list of citations in the given file.
    """
    driver = set_up_selenium(browser='chrome')

    patentData = []
    patentCitations = []
    non_patent_citations = []
    data_cited_by = []

    timeouts_data = []
    for index, row in df.iterrows():
        if index > 100:
            continue
        print(f"{index}/{df.shape[0]}")
        number = row['patentID'].replace(" ", "")
        url = f"https://patents.google.com/patent/{number}/en?oq={number}"
        try:
            driver.get(url)
        except TimeoutException:
            print('timeout')
            timeouts_data.append(number)
            continue
        except WebDriverException:
            print('webdriver')
            timeouts_data.append(number)
            continue
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "footer"))
            )
        except TimeoutException:
            print('Loading took too much time!')
            continue
        except WebDriverException:
            print('webdriver')
            timeouts_data.append(number)
            continue

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        abstract_div = soup.find('div', class_='abstract style-scope patent-text')
        if not abstract_div:
            url = f"https://patents.google.com/patent/{number}A1/"
            try:
                driver.get(url)
            except TimeoutException:
                print('timeout')
                timeouts_data.append(number)
                continue
            except WebDriverException:
                print('webdriver')
                timeouts_data.append(number)
                continue
            try:
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "footer"))
                )
            except TimeoutException:
                print('Loading took too much time!')
                continue
            except WebDriverException:
                print('webdriver')
                timeouts_data.append(number)
                continue
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            abstract_div = soup.find('div', class_='abstract style-scope patent-text')

        abstract = abstract_div.text.strip().replace(";", " ").replace("\n", " ").replace("\t", " ")
        status_div = soup.find('div', class_='legal-status style-scope application-timeline', string="Status")
        status = status_div.find_next('span', class_='title-text style-scope application-timeline').text.strip()
        claim_id = soup.find('section', id='claims')
        claim_text = ""
        for claim in claim_id.find_all('claim'):
            claim_text += claim.text.strip().replace(";", " ").replace("\n", " ").replace("\t", " ") + " "

        patent_data = {
            "publication_number": number,
            "status": status,
            "abstract": abstract,
            "claims": claim_text
        }
        patentData.append(patent_data)

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
        # sleep_time(1)

    # if timeouts_data:
    #     for index, number in enumerate(timeouts_data):
    #         print(f"{index}/{len(publication_numbers)}", year_path)
    #         print('number', number)
    #         url = f"https://patents.google.com/patent/{number}/en?oq={number}"
    #         try:
    #             driver.get(url)
    #         except TimeoutException:
    #             print('timeout')
    #             continue
    #         except WebDriverException:
    #             print('webdriver')
    #             continue
    #         try:
    #             WebDriverWait(driver, 5).until(
    #                 EC.visibility_of_element_located((By.CLASS_NAME, "footer"))
    #             )
    #         except TimeoutException:
    #             print('Loading took too much time!')
    #             continue
    #         except WebDriverException:
    #             print('webdriver')
    #             continue

    #         html = driver.page_source
    #         soup = BeautifulSoup(html, 'html.parser')

    #         if not soup.find('h3', id='patentCitations'):
    #             citation = {
    #                 "publication_number": number,
    #                 "patent_citation": 0,
    #                 "publication_date": 0,
    #                 "assignee": 0,
    #                 "title": 0
    #             }
    #             patentCitations.append(citation)
    #         else:
    #             citations = get_data_tables(soup, number, 'patentCitations')
    #             patentCitations.extend(iter(citations))

    #         if not soup.find('h3', id='citedBy'):
    #             citation = {
    #                 "publication_number": number,
    #                 "patent_citation": 0,
    #                 "publication_date": 0,
    #                 "assignee": 0,
    #                 "title": 0
    #             }
    #             data_cited_by.append(citation)
    #         else:
    #             citedBy_s = get_data_tables(soup, number, 'citedBy')
    #             data_cited_by.extend(iter(citedBy_s))

    #         if not soup.find('h3', id='nplCitations'):
    #             citation = {
    #                 "publication_number": number,
    #                 "patent_citation": 0,
    #                 "publication_date": 0,
    #                 "assignee": 0,
    #                 "title": 0
    #             }
    #             non_patent_citations.append(citation)
    #         else:
    #             h3_pc = soup.find('h3', id='nplCitations')
    #             pc_table = h3_pc.find_next('div', class_='responsive-table')
    #             for tr in pc_table.find_all('div', class_='tr')[1:]:
    #                 citation = {
    #                     "publication_number": number,
    #                     "patent_citation": 0,
    #                     "publication_date": 0,
    #                     "assignee": 0,
    #                     "title": tr.text.replace('*', '').strip()
    #                 }
    #                 non_patent_citations.append(citation)
            # sleep_time(1)
    driver.quit()

    df_patentCitations = pd.DataFrame(patentCitations)
    df_non_patent_citations = pd.DataFrame(non_patent_citations)
    df_data_cited_by = pd.DataFrame(data_cited_by)
    df_patent_data = pd.DataFrame(patentData)
    output_name = "all_patents"
    output_file = os.path.join(output_citations, f"{output_name}_citations.xlsx")
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    df_patentCitations.to_excel(writer, sheet_name='PatentCitations', index=False)
    df_non_patent_citations.to_excel(writer, sheet_name='NonPatentCitations', index=False)
    df_data_cited_by.to_excel(writer, sheet_name='CitedBy', index=False)
    df_patent_data.to_excel(writer, sheet_name='PatentData', index=False)
    writer.save()
    writer.close()

    if not os.path.exists(citation_csv):
        os.makedirs(citation_csv)
    year_folder = os.path.join(citation_csv, output_name)
    if not os.path.exists(year_folder):
        os.makedirs(year_folder)
    df_patentCitations.to_csv(os.path.join(year_folder, f"{output_name}_PatentCitations.csv"), index=False, sep=';')
    df_non_patent_citations.to_csv(os.path.join(year_folder, f"{output_name}_NonPatentCitations.csv"), index=False, sep=';')
    df_data_cited_by.to_csv(os.path.join(year_folder, f"{output_name}_CitedBy.csv"), index=False, sep=';')
    df_patent_data.to_csv(os.path.join(year_folder, f"{output_name}_PatentData.csv"), index=False, sep=';')


if __name__ == '__main__':
    # Read the data
    df = pd.read_csv('7171patentData.csv', sep=";")
    # Print the first 5 rows
    print(df.shape)
    get_citations(df)