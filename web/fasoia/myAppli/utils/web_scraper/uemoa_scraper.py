import requests
from bs4 import BeautifulSoup  
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

def scraping(objects):
    data =[]
    for element in objects:
        description =element.find('p', class_ ="pb-2").text
        date_limite =element.find('time').text
        download_url =element.find('a')['href']
        
        data.append(
            {
                'description' : description,
                'date_limite' : date_limite,
                'download_url': download_url
            }
        )
        print("Description: "+description+"\nDate limite: "+date_limite+"\nTélécharger: "+download_url+"\n")
    return data  

def scraper(base_url):
    headers = {
            'User-Agent': 'Mozilla/5.0'
        }
    current_url =base_url
    all_data =[]
    while current_url:
        page = requests.get(
            current_url,
            headers=headers,
            verify=False,
            timeout=10
        )
        #print(page.status_code)
        soup =BeautifulSoup(page.text, 'html.parser')
        dom_objects =soup.find_all('div', class_ ="news-box mb-2 px-1")
        all_data.extend(scraping(dom_objects))
        next_li_element =soup.find('a', class_ ="next")
        if next_li_element:
            next_page_relative_url = next_li_element.find('li', href=True)['href']
            current_url =urljoin(current_url, next_page_relative_url)
        else:
            current_url =None
    return all_data        
