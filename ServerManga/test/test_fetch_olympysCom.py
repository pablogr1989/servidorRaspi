import requests
from bs4 import BeautifulSoup

url = 'https://olympusbiblioteca.com/series/comic-27-220-225-565464565465'
response = requests.get(url, timeout=10)

print(response.content)
print("\n\n\n\n\n\n\n\n")

soup = BeautifulSoup(response.content, 'html.parser')

all_divs = soup.find_all('div')
for div in all_divs[:20]:  # Primeros 20
    print(div.get('class'))

grids = soup.find_all('div', class_='grid')
print(f"Grids encontrados: {len(grids)}")

chapter_links = soup.find_all('a', href=lambda x: x and '/capitulo/' in x)
print(f"Links capitulos: {len(chapter_links)}")

if chapter_links:
    print("\nPrimer link:")
    print(chapter_links[0].prettify()[:500])