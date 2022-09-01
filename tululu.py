import argparse
import requests
import os
import sys
import time
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename, sanitize_filepath
from urllib.parse import urljoin, urlsplit, urlparse, unquote
from tqdm import tqdm


DOMAIN = 'https://tululu.org/'
VERSION = "1.0"
reconnection_counter = 0


def check_for_redirect(response, domain):
    if response.history:
        raise requests.exceptions.HTTPError


def download_txt(url, params, filename, folder='./books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    os.makedirs(folder, exist_ok=True)
    filepath = sanitize_filepath(os.path.join(folder, f'{filename}.txt'))
    success_connection = False
    global reconnection_counter

    while not success_connection:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            check_for_redirect(response, DOMAIN)
            success_connection = True
            reconnection_counter == 0

            with open(filepath, 'wb') as file:
                file.write(response.content)

            return filepath
        except requests.exceptions.HTTPError:
            print(f'HTTPError. The book id {params["id"]} is not exists', file=sys.stderr)
            success_connection = True

        except requests.exceptions.ConnectionError:
            if reconnection_counter == 0:
                print('ConnetionError. Reconnection attempt', file=sys.stderr)
                reconnection_counter = reconnection_counter + 1
                download_txt(url, params, filename, folder)
            else:
                print('ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                time.sleep(3)
                reconnection_counter = reconnection_counter + 1
                download_txt(url, params, filename, folder)


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
    filepath = sanitize_filepath(os.path.join(folder, filename))
    success_connection = False
    global reconnection_counter
    
    while not success_connection:
        try:
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response, DOMAIN)

            with open(filepath, 'wb') as file:
                file.write(response.content)

            return filepath
        except requests.exceptions.HTTPError:
            print(f'HTTPError. The picture is not exists', file=sys.stderr)
            success_connection = True

        except requests.exceptions.ConnectionError:
            if reconnection_counter == 0:
                print('ConnetionError. Reconnection attempt', file=sys.stderr)
                reconnection_counter = reconnection_counter + 1
                download_image(url, filename, folder)
            else:
                print('ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                time.sleep(3)
                reconnection_counter = reconnection_counter + 1
                download_image(url, filename, folder)


def parse_book_page(html):

    soup = BeautifulSoup(html, 'lxml')
    title_book = soup.select('#content h1')[0]
    title, author = title_book.text.split(sep='::')
    img_src = soup.find(class_='bookimage').find('img')['src']
    img_name = urlsplit(img_src)[2].split(sep='/')[-1]
    genres = soup.find('span', class_='d_book').find_all('a')
    comments = soup.find_all(class_='texts')

    book = {
        'title': title.strip(),
        'author': author.strip(),
        'img_src': img_src,
        'img_name': img_name,
        'genres': [genre.text for genre in genres],
        'comments': [comment.find(class_='black').text for comment in comments],
    }

    return book


def create_parser ():
    parser = argparse.ArgumentParser(
            prog = 'Parser of library https://tululu.org/',
            description = '''Parser for information about a book and download''',
            epilog = '''(c) SVA 2022 GNU licensed'''
    )

    parser.add_argument ('start_id', nargs='?', type=int, default=1, help="books id for start position of downloading")
    parser.add_argument ('end_id', nargs='?', type=int, default=11, help="books id for end position of downloading")
    parser.add_argument ('--version',
            action='version',
            help = 'Вывести номер версии',
            version='%(prog)s {}'.format (VERSION))
 
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    global reconnection_counter


    for book_id in tqdm(range(args.start_id, args.end_id)):
        success_connection = False
        while not success_connection:
            try:
                url = f'{DOMAIN}b{book_id}/'
                response = requests.get(url)
                response.raise_for_status()
                check_for_redirect(response, DOMAIN)
                success_connection = True
                book = parse_book_page(response.text)

                params = {"id": book_id}
                url_book = f'{DOMAIN}txt.php'
                download_txt(url_book, params, f"{book_id}. {book['title']}")
                download_image(urljoin(DOMAIN, book['img_src']), book['img_name'])

            except requests.exceptions.HTTPError:
                print(f'HTTPError. The book id {book_id} is not exists', file=sys.stderr)
                success_connection = True

            except requests.exceptions.ConnectionError:
                if reconnection_counter == 0:
                    print('ConnetionError. Reconnection attempt', file=sys.stderr)
                    reconnection_counter = reconnection_counter + 1
                else:
                    print('ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                    time.sleep(3)
                    reconnection_counter = reconnection_counter + 1


if __name__ == "__main__":
    main()
