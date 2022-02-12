from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename, sanitize_filepath
from urllib.parse import urljoin, urlsplit, urlparse, unquote
from tqdm import tqdm
import argparse
import requests
import os


DOMAIN = 'https://tululu.org/'
VERSION = "1.0"


def check_for_redirect(response, domain):
    if response.history and response.url == domain:
        raise requests.exceptions.HTTPError


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
    check_for_redirect(response, DOMAIN)

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
    check_for_redirect(response, DOMAIN)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath

def parse_book_page(html):
    book_info = {}

    soup = BeautifulSoup(html, 'lxml')
    title_book = soup.select('#content h1')[0]
    name, author = title_book.text.split(sep='::')[0].strip(), title_book.text.split(sep='::')[1].strip()
    img_src = soup.find(class_='bookimage').find('img')['src']
    img_name = urlsplit(img_src)[2].split(sep='/')[-1]
    genres = soup.find('span', class_='d_book').find_all('a')
    comments = soup.find_all(class_='texts')

    book_info['name'] = name
    book_info['author'] = author
    book_info['img_src'] = img_src
    book_info['img_name'] = img_name
    book_info['genres'] = []
    book_info['comments'] = []

    for genre in genres:
        book_info['genres'].append(genre.text)

    for comment in comments:
        book_info['comments'].append(comment.find(class_='black').text)

    return book_info


def create_parser ():
    parser = argparse.ArgumentParser(
            prog = 'Parser of library https://tululu.org/',
            description = '''Parser for information about a book and download''',
            epilog = '''(c) SVA 2022 GNU licensed'''
    )

    parser.add_argument ('start_id', nargs='?', type=int, default=1, help="books id for start position of downloading")
    parser.add_argument ('end_id', nargs='?', type=int, default=10, help="books id for end position of downloading")
    parser.add_argument ('--version',
            action='version',
            help = 'Вывести номер версии',
            version='%(prog)s {}'.format (VERSION))
 
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    for book_id in tqdm(range(args.start_id, args.end_id)):
        try:
            url = f'{DOMAIN}b{book_id}/'
            response = requests.get(url)
            response.raise_for_status()
            
            check_for_redirect(response, DOMAIN)
            book_info = parse_book_page(response.text)
            print(book_info)

            url_book = f'{DOMAIN}txt.php?id={book_id}'
            download_txt(url_book, str(book_id) + '. ' + book_info['name'])
            download_image(urljoin(DOMAIN, book_info['img_src']), book_info['img_name'])

        except requests.exceptions.HTTPError:
            print(f'HTTPError. The book id {book_id} is not exists')


if __name__ == "__main__":
    main()
