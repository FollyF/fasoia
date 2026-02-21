import requests
from bs4 import BeautifulSoup  

headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}
url ='https://quotes.toscrape.com'
page = requests.get(url, headers=headers)
print(page.status_code)
soup =BeautifulSoup(page.text, 'html.parser')
quotes_list =soup.find_all('div', class_ ="quote")
quotes =[]
for quote in quotes_list:
    text =quote.find('span', class_ ="text").text
    author =quote.find('small', class_ ="author").text
    tags_list =quote.select(".tags .tag")
    tags =[]
    for tag in tags_list:
        tags.append(tag.get_text(strip=True))
    quotes.append(
        {
            'text' : text,
            'author' : author,
            'tags': ', '.join(tags)
        }
    )
for quote in quotes:
    print("Texte: "+quote['text']+"\nAuthor: "+quote['author']+"\nTags: "+quote['tags']+"\n")
