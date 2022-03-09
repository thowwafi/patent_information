import base64
from bs4 import BeautifulSoup
import io
import os
import requests
from selenium.webdriver.common.by import By
from utils import set_up_selenium, sleep_time
from PIL import UnidentifiedImageError
import PIL.Image as Image


NORWAY_URL = "https://kolbiss.jira.com/wiki/spaces/IM/overview"
NORWAY_FOLDER_PATH = os.path.join(os.getcwd(), 'imageDesk', 'Norway')
SWEDIAN_URL = "https://kolbiss.jira.com/wiki/spaces/IG/overview"
SWEDIAN_FOLDER_PATH = os.path.join(os.getcwd(), 'imageDesk', 'Sweden')

URL = NORWAY_URL
PATH = NORWAY_FOLDER_PATH


def get_file_content_chrome(driver, uri):
    result = driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
    if type(result) == int :
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)


def main(url):
    driver = set_up_selenium(browser='firefox')
    driver.get(url)
    sleep_time(1)
    print(driver.title)
    print(driver.current_url)
    
    urls = []
    for a in driver.find_elements(By.TAG_NAME, 'a'):
        if a is not None:
            if a.get_attribute('href'):
                if a.get_attribute('href').startswith('https') and "#" not in a.get_attribute('href'):
                    urls.append(a.get_attribute('href'))

    for url_ in urls:
        driver.get(url_)
        sleep_time(2)
        if "id.atlassian.com" in driver.current_url:
            print("continue")
            continue
        html = driver.page_source
        print(url_)
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        url_folder = os.path.join(PATH, url_.split('/')[-1])
        if not os.path.exists(url_folder):
            os.makedirs(url_folder)
        for index, img in enumerate(images):
            # print('img', img)
            src_img = img.get('src')
            if src_img.startswith('/'):
                print('continue', src_img)
                continue
            print('src_img', src_img)
            img_name = img.parent.get('data-test-media-name')
            if not img_name:
                img_name = index

            if 'svg' in src_img:
                svg = requests.get(url).text
                path = os.path.join(url_folder, f'{img_name}.svg')
                with open(path, 'w') as file:
                    file.write(svg)
            elif 'blob' in src_img:
                try:
                    img_bytes = get_file_content_chrome(driver, src_img)
                except Exception as e:
                    print('continue', src_img)
                    continue
                try:
                    image = Image.open(io.BytesIO(img_bytes))
                except UnidentifiedImageError:
                    print('continue', src_img)
                    continue
                    
                rgb_im = image.convert('RGB')
                rgb_im.save(os.path.join(url_folder, f'{img_name}.jpg'))

            else:
                path = os.path.join(url_folder, f'{img_name}.jpg')
                with open(path, 'wb') as handle:
                    response = requests.get(src_img, stream=True)

                    if not response.ok:
                        print(response)

                    for block in response.iter_content(1024):
                        if not block:
                            break

                        handle.write(block)

        html_path = os.path.join(url_folder, url_.split('/')[-1])
        with open(f"{html_path}.html", "w") as f:
            f.write(html)
    driver.close()


if __name__ == '__main__':
    main(URL)
