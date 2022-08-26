import re
import os
import requests
import json
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathvalidate import sanitize_filename, sanitize_filepath
from tululu import download_txt, parse_book_page, download_image, check_for_redirect


DOMAIN = "https://tululu.org/"
VERSION = "1.0"


def download_category(url_category, start_page, end_page, books_folder='./books/', images_folder="./img"):
    """Функция для скачивания категорий книг.
    Args:
        category_number (int): id категории, которую собираетесь скачать
        start_page (int): начиная с какой страницы скачивать книги
        end_page (int): заканчивая какой страницей скачивать книги 
        books_folder (str): Папка, куда сохранять книги
        images_folder (str): Папка, куда сохранять обложки книг
    Returns:
        str: ссылки на скаченные книги
    """

    books_info = []

    for page in range(start_page, end_page):
        response = requests.get(urljoin(url_category, str(page)))
        response.raise_for_status()
        check_for_redirect(response, DOMAIN)

        soup = BeautifulSoup(response.text, "lxml")
        books_links = soup.select(".d_book .bookimage a")

        for book_link in books_links:
            book_href = book_link["href"]
            book_id = re.search("\d+", book_href)[0]

            try:
                book_url = urljoin(DOMAIN, book_href)
                response = requests.get(book_url)
                book_info = parse_book_page(response.text)
                book_info["book_path"] = f'{sanitize_filepath(os.path.join(books_folder, sanitize_filename(book_info["title"])))}.txt'
                params = {"id": book_id}
                book_url_txt = f'{DOMAIN}txt.php'

                
                download_txt(book_url_txt, params, book_info['title'], books_folder)
                download_image(urljoin(DOMAIN, book_info['img_src']), book_info['img_name'], images_folder)
                books_info.append(book_info)
                print(book_url)

            except requests.exceptions.HTTPError:
                print(f'HTTPError. The book id {book_id} is not exists')


            book_info_json = json.dumps(books_info, ensure_ascii=False, indent=4)
            with open("books.json", "w", encoding='utf8') as books:
                books.write(book_info_json)


def get_number_pages(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response, DOMAIN)

    soup = BeautifulSoup(response.text, "lxml")
    npage = soup.select(".npage")[-1].text

    return int(npage)

def create_parser():
    parser = argparse.ArgumentParser(
            prog = 'Parser of books category from library https://tululu.org/',
            description = '''Parser for category of books and downloading''',
            epilog = '''(c) SVA 2022 GNU licensed'''
    )
    parser.add_argument ('--id', nargs='?', type=int, default=55, help="Id of books category")
    parser.add_argument ('--start_page', nargs='?', type=int, default=1, help="Page number for start of downloading from category")
    parser.add_argument ('--end_page', nargs='?', type=int, default=None, help="Page number for finish of downloading from category")
    parser.add_argument ('--version',
            action='version',
            help = 'Вывести номер версии',
            version='%(prog)s {}'.format (VERSION))
 
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    url = f"https://tululu.org/l{args.id}/"
    npage = get_number_pages(url)

    try:
        if args.end_page > npage:
            args.end_page = npage
    except TypeError:
        args.end_page = npage

    download_category(url, args.start_page, args.end_page)

if __name__ == "__main__":
    main()