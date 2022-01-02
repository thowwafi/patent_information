from bs4 import BeautifulSoup
import requests


AUTH_URL = "https://data.epo.org/pise-server/rest/authentication?request.preventCache=1641083513865"
SEACRH_URL = "https://data.epo.org/pise-server/rest/searches?request.preventCache=1641084355766"

def main():
    payload = {'login': 'guest', 'password': 'guest'}
    session = requests.Session()
    resp = session.post(AUTH_URL, data=payload)
    xmlstring = resp.text

    soup = BeautifulSoup(xmlstring, 'lxml')
    token = soup.find('token').text

    payload2 = {
        'databaseId': 'EPAB2021052',
        'q': 'APPCO%20%3D%20NL%20AND%20APD%20%3E%3D%202000',
        'synchronous': 'false',
        'estimate': 'false',
        'termConnector': 'OR',
        'criteriaConnector': 'OR',
    }
    resp2 = session.post(SEACRH_URL, data=payload2, headers={'Authentication-Token': token})
    xmlstring = resp2.text
    soup = BeautifulSoup(xmlstring, 'lxml')
    status_id = soup.find('resourceuuid').text
    print('status', status_id)

    results_url = f"https://data.epo.org/pise-server/rest/searches/{status_id}/results?position=0&size=30&field=HIT_LIST&synchronous=false&request.preventCache=1641108532638"
    # result_url = f"https://data.epo.org/pise-server/rest/statuses/{status_id}?request.preventCache=1641089355766"
    print('token', token)
    print(results_url)
    resp3 = session.get(results_url, headers={
        'Authentication-Token': token, 
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    })
    print(resp3)

    url = "https://data.epo.org/pise-server/rest/statuses/033f1d4a-2157-4c13-907f-a8b40a40403d%2C?request.preventCache=1641108533708"
    resp4 = session.get(url, headers={
        'Authentication-Token': token, 
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    })
    print(resp4)
    import pdb; pdb.set_trace()
    xmlstring = resp2.text
    soup = BeautifulSoup(xmlstring, 'lxml')


if __name__ == '__main__':
    main()