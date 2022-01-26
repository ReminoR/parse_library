import requests
from bs4 import BeautifulSoup

url = 'https://www.franksonnenbergonline.com/blog/are-you-grateful/'
response = requests.get(url)
response.raise_for_status()


soup = BeautifulSoup(response.text, 'lxml')

title_tag = soup.find('h1', class_="entry-title")

img_src = soup.find('img', class_="attachment-post-image")['src']

desc_post = soup.find('div', class_="entry-content")

print(desc_post.text)