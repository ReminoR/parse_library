import requests
import os


dir = './books/'
os.makedirs(dir, exist_ok=True)

for id in range(1, 10):
    url = 'https://tululu.org/txt.php?id=32168'
    response = requests.get(url)
    response.raise_for_status()
    
    filename = str(id) + '.txt'
    with open(dir + filename, 'wb') as file:
        file.write(response.content)