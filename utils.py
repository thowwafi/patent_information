import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.support.ui import Select
import time
import wget
import zipfile


def sleep_time(number):
    for i in range(number, 0, -1):
        print(f"{i}", end='\n', flush=True)
        time.sleep(1)


def set_up_selenium():
    options = ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    home = os.getcwd()
    driver_path = os.path.join(home, 'webdriver', 'mac', 'chromedriver')
    try:
        return webdriver.Chrome(options=options, executable_path=driver_path)
    except SessionNotCreatedException as e:
        message = str(e)
        print(message)
        version_number = message.split('version is ')[1][:12]
        download_url = "https://chromedriver.storage.googleapis.com/" + version_number +"/chromedriver_linux64.zip"
        print(download_url)
        latest_driver_zip = wget.download(download_url, 'chromedriver.zip')
        print(latest_driver_zip)
        path = os.path.join(home, 'webdriver', 'mac')
        with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
            zip_ref.extractall(path)
        os.remove(latest_driver_zip)
        return webdriver.Chrome(options=options, executable_path=driver_path)
