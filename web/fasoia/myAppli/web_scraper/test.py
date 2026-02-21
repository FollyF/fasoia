import requests
from bs4 import BeautifulSoup  
from urllib.parse import urljoin

headers = {
    'User-Agent': 'Mozilla/5.0'
    }

def scraping(objects):
    donnees =[]
    for element in objects:
        text =element.find('span', class_ ="text").text
        author =element.find('small', class_ ="author").text
        tags_list =element.select(".tags .tag")
        tags =[]
        for tag in tags_list:
            tags.append(tag.get_text(strip=True))
        donnees.append(
            {
                'text' : text,
                'author' : author,
                'tags': ', '.join(tags)
            }
        )
    for donnee in donnees:
        print("Page \n"+"Texte: "+donnee['text']+"\nAuthor: "+donnee['author']+"\nTags: "+donnee['tags']+"\n")
        

def scraper(base_url, headers):
    current_url =base_url
    while current_url:
        page = requests.get(current_url, headers=headers)
        #print(page.status_code)
        soup =BeautifulSoup(page.text, 'html.parser')
        dom_objects =soup.find_all('div', class_ ="quote")
        scraping(dom_objects)
        next_li_element =soup.find('li', class_ ="next")
        if next_li_element:
            next_page_relative_url = next_li_element.find('a', href=True)['href']
            current_url =urljoin(current_url, next_page_relative_url)
        else:
            current_url =None
                

if __name__ == "__main__":
    base_url ='https://quotes.toscrape.com'
    scraper(base_url, headers)