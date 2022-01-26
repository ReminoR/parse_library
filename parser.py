from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename, sanitize_filepath
import requests
import os

domain = 'https://tululu.org/'

def check_for_redirect(response, domain):
    if response.history and response.url == domain:
        raise requests.exceptions.HTTPError
    return


def download_txt(url, filename, folder='./books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    os.makedirs(folder, exist_ok=True)
    filepath = sanitize_filepath(os.path.join(folder, sanitize_filename(filename + '.txt')))
    
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response, domain)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath




for id in range(1, 11):
    try:
        url = domain + 'b' + str(id) + '/'
        response = requests.get(url)
        check_for_redirect(response, domain)

        soup = BeautifulSoup(response.text, 'lxml')
        title_book = soup.select('#content h1')
        name = title_book[0].text.split(sep='::')[0].strip()
        author = title_book[0].text.split(sep='::')[1].strip()

        url = domain + 'txt.php?id=' + str(id)
        download_txt(url, str(id) + '. ' + name)
        
    except requests.exceptions.HTTPError:
        print("HTTPError")



