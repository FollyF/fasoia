import requests
from bs4 import BeautifulSoup  
from urllib.parse import urljoin

def scraping(objects):
    data =[]
    for element in objects:
        text =element.find('span', class_ ="text").text
        author =element.find('small', class_ ="author").text
        tags_list =element.select(".tags .tag")
        tags =[]
        for tag in tags_list:
            tags.append(tag.get_text(strip=True))
        data.append(
            {
                'text' : text,
                'author' : author,
                'tags': ', '.join(tags)
            }
        )
        print("Texte: "+text+"\nAuthor: "+author+"\nTags: "+str(tags)+"\n")
    return data  

def scraper(base_url):
    headers = {
            'User-Agent': 'Mozilla/5.0'
        }
    current_url =base_url
    all_data =[]
    while current_url:
        page = requests.get(current_url, headers=headers)
        #print(page.status_code)
        soup =BeautifulSoup(page.text, 'html.parser')
        dom_objects =soup.find_all('div', class_ ="quote")
        all_data.extend(scraping(dom_objects))
        next_li_element =soup.find('li', class_ ="next")
        if next_li_element:
            next_page_relative_url = next_li_element.find('a', href=True)['href']
            current_url =urljoin(current_url, next_page_relative_url)
        else:
            current_url =None
    return all_data        
