
from bs4 import BeautifulSoup
from datetime import timedelta
from main import get_patent_data
import pandas as pd
import requests
import sys
import time
from timeit import default_timer as timer


AUTH_URL = "https://data.epo.org/pise-server/rest/authentication"
SEACRH_URL = "https://data.epo.org/pise-server/rest/searches"
DATABASE_ID = 'EPAB2022002'


def check():
    for year in range(2000, 2022):
        print(f'{year}')
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

        result_url = f"https://data.epo.org/pise-server/rest/searches/{status_id}/results?position=0&size=10000&field=HIT_LIST&synchronous=false&request.preventCache=1642141615116"
        resp4 = session.get(result_url, headers=headers)
        while resp4.status_code == 404:
            time.sleep(1)
            resp4 = session.get(result_url, headers=headers)

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

        df = pd.read_excel(f'output/patents_{year}.xlsx')
        print("len df", len(df))

        print(len(df) == len(row_data))

        print("----------------")
    return

if __name__ == '__main__':
    check()
