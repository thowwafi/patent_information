import os
from selenium.webdriver.common.by import By
from utils import set_up_selenium, sleep_time


NORWAY_URL = "https://kolbiss.jira.com/wiki/spaces/IM/overview"
NORWAY_FOLDER_PATH = os.path.join(os.getcwd(), 'imageDesk', 'Norway')
SWEDIAN_URL = "https://kolbiss.jira.com/wiki/spaces/IG/overview"
SWEDIAN_FOLDER_PATH = os.path.join(os.getcwd(), 'imageDesk', 'Sweden')

def main(url):
    driver = set_up_selenium(browser='firefox')
    driver.get(url)
    sleep_time(2)
    print(driver.title)
    print(driver.current_url)
    # print(driver.page_source)
    # find all a tags hrefs
    html = driver.page_source
    html_path = os.path.join(SWEDIAN_FOLDER_PATH, driver.current_url.split('/')[-1])
    with open(f"{html_path}.html", "w") as f:
        f.write(html)
    
    urls = []
    for a in driver.find_elements(By.TAG_NAME, 'a'):
        if a is not None:
            if a.get_attribute('href'):
                if a.get_attribute('href').startswith('https') and "#" not in a.get_attribute('href'):
                    urls.append(a.get_attribute('href'))

    for url_ in urls:
        print(url_)
        driver.get(url_)
        sleep_time(7)
        if "id.atlassian.com" in driver.current_url:
            print("continue")
            continue
        html = driver.page_source
        html_path = os.path.join(SWEDIAN_FOLDER_PATH, url_.split('/')[-1])
        with open(f"{html_path}.html", "w") as f:
            f.write(html)
    driver.close()


if __name__ == '__main__':
    main(SWEDIAN_URL)
