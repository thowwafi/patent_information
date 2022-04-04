import os
import platform
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FOptions
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.support.ui import Select
import time
import wget
from xml.etree import ElementTree
import zipfile


def sleep_time(number):
    for i in range(number, 0, -1):
        print(f"{i}", end='\n', flush=True)
        time.sleep(1)


def set_up_selenium(browser='chrome'):
    options = ChromeOptions() if browser == 'chrome' else FOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    home = os.getcwd()
    system = platform.system().lower()
    if browser == 'chrome':
        driver_path = os.path.join(home, 'webdriver', system, 'chromedriver')
        try:
            return webdriver.Chrome(options=options, executable_path=driver_path)
        except SessionNotCreatedException as e:
            message = str(e)
            print(message)
            version_number = message.split('version is ')[1][:12]
            version_num = version_number.split('.')[0]
            url = 'https://chromedriver.storage.googleapis.com/'
            response = requests.get(url, stream=True)
            response.raw.decode_content = True
            events = ElementTree.iterparse(response.raw)
            for _, elem in events:
                if elem.tag == "{http://doc.s3.amazonaws.com/2006-03-01}Key" and elem.text.startswith(version_num) and 'linux' in elem.text:
                    print('found the right version')
                    version_number = elem.text
                    break
            download_url = "https://chromedriver.storage.googleapis.com/" + version_number
            print(download_url)
            latest_driver_zip = wget.download(download_url, 'chromedriver.zip')
            print(latest_driver_zip)
            path = os.path.join(home, 'webdriver', 'mac')
            with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
                zip_ref.extractall(path)
            os.remove(latest_driver_zip)
            return webdriver.Chrome(options=options, executable_path=driver_path)
    else:
        driver_path = os.path.join(home, 'webdriver', system, 'geckodriver')
        return webdriver.Firefox(options=options, executable_path=driver_path)
