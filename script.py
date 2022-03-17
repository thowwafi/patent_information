#!/venv/bin/python

import pdb
from bs4 import BeautifulSoup
from datetime import timedelta
from main import get_patent_data, get_patent_datas
import pandas as pd
import requests
import sys
import time
from timeit import default_timer as timer


AUTH_URL = "https://data.epo.org/pise-server/rest/authentication"
SEACRH_URL = "https://data.epo.org/pise-server/rest/searches"
DATABASE_ID = 'EPAB2022008'

def main(year):
    headers = {'Accept': 'application/json'}
    payload = {'login': 'guest', 'password': 'guest'}
    session = requests.Session()
    resp = session.post(AUTH_URL, data=payload, headers=headers)
    token = resp.json().get('token')

    payload2 = {
        'databaseId': DATABASE_ID,
        'q': f'APPCO = NL AND APD > {year} AND APD < {year + 1}',
        'synchronous': 'false',
        'estimate': 'false',
        'termConnector': 'OR',
        'criteriaConnector': 'OR',
    }
    headers['Authentication-Token'] = token
    resp2 = session.post(SEACRH_URL, data=payload2, headers=headers)
    status_id = resp2.json().get('id')
    print('resp2', resp2)
    print('status', status_id)

    result_url = f"https://data.epo.org/pise-server/rest/searches/{status_id}/results?position=0&size=10000&field=HIT_LIST&synchronous=false&request.preventCache=1642141615116"
    resp4 = session.get(result_url, headers=headers)
    print('resp4', resp4.status_code)
    while resp4.status_code == 404:
        time.sleep(1)
        resp4 = session.get(result_url, headers=headers)
        print('resp4', resp4.status_code)

    result_id = resp4.json().get('id')

    final_url = f"https://data.epo.org/pise-server/rest/statuses/{result_id}"
    final_res = session.get(final_url, headers=headers)
    print('final_res', final_res.json().get('state'))
    while final_res.json().get('state') == 'RUNNING':
        time.sleep(1)
        final_res = session.get(final_url, headers=headers)
        print('final_res', final_res.json().get('state'))

    headers.pop('Accept')
    row_data = final_res.json().get('resource').get('results').get('rowData')
    print("total", len(row_data))
    patents = []
    for index, row in enumerate(row_data):
        print('iter', year, f'{index}/{len(row_data)}')
        key = row.get('key')
        patent_url = f"https://data.epo.org/pise-server/rest/databases/{DATABASE_ID}/documents/{key}?section=BIBLIOGRAPHIC_DATA"
        patent_res = session.get(patent_url, headers=headers)
        soup = BeautifulSoup(patent_res.content, 'html.parser')
        patents_data = get_patent_datas(soup)
        for patent in patents_data:
            patents.append(patent)

    newdf = pd.DataFrame(patents)
    newdf.to_excel(f'output_excel/patents_{year}.xlsx', index=False)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please specify year')
        sys.exit()
    year_from = int(sys.argv[1])
    year_to = int(sys.argv[2])
    years = list(range(year_from, year_to))
    # years = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
    for year in years:
        start = timer()
        main(year)
        end = timer()
        print(timedelta(seconds=end-start))
    print('done')
