from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename, sanitize_filepath
from urllib.parse import urljoin, urlsplit, urlparse, unquote
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


def download_image(url, filename, folder="./img"):
    """Функция для скачивания графических файлов.
    Args:
        url (str): Cсылка на изображение, которое хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранено изображение.
    """

    os.makedirs(folder, exist_ok=True)
    filepath = sanitize_filepath(os.path.join(folder, sanitize_filename(filename)))
    
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response, domain)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def main():
    for id in range(1, 11):
        try:
            url = domain + 'b' + str(id) + '/'
            response = requests.get(url)
            check_for_redirect(response, domain)

            soup = BeautifulSoup(response.text, 'lxml')
            title_book = soup.select('#content h1')
            name = title_book[0].text.split(sep='::')[0].strip()
            author = title_book[0].text.split(sep='::')[1].strip()
            url_book = domain + 'txt.php?id=' + str(id)
            img_src = soup.find(class_='bookimage').find('img')['src']
            img_name = urlsplit(img_src)[2].split(sep='/')[-1]
            genres = soup.find('span', class_='d_book').find_all('a')
            
            print(name)
            # for genre in genres:
                # print(genre.text)

            for comment in soup.find_all(class_='texts'):
                print(comment.find(class_='black').text)
            print("\n\r")
            # download_txt(url_book, str(id) + '. ' + name)
            # download_image(urljoin(domain, img_src), img_name)

        except requests.exceptions.HTTPError:
            print("HTTPError")


if __name__ == "__main__":
    main()
