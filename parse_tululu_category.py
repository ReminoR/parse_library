import re
import os
import requests
import json
import argparse
import sys
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathvalidate import sanitize_filename, sanitize_filepath
from tqdm import tqdm
from tululu import download_txt, parse_book_page, download_image, check_for_redirect


DOMAIN = "https://tululu.org/"
VERSION = "1.0"
reconnection_counter = 0


def get_number_pages(url):
    """Функция получает количество страниц в категории или автора
    Args:
        url (int): url категории
    Returns:
        int: количество страниц в категории
    """
    global reconnection_counter
    success_connection = False

    while not success_connection:
        try:
            response = requests.get(url)
            response.raise_for_status()
            success_connection = True
            reconnection_counter == 0

            soup = BeautifulSoup(response.text, "lxml")
            pages = soup.select(".npage")
            if pages:
                npage = int(soup.select(".npage")[-1].text)
            else:
                npage = 1

            return npage
        except requests.exceptions.HTTPError:
            print(f'HTTPError. The page is not exists', file=sys.stderr)
            quit()

        except requests.exceptions.ConnectionError:
            if reconnection_counter == 0:
                print('Get number page is failed. ConnetionError. Reconnection attempt', file=sys.stderr)
                reconnection_counter = reconnection_counter + 1
                get_number_pages(url)  
            else:
                print('Get number page is failed. ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                time.sleep(3)
                reconnection_counter = reconnection_counter + 1
                get_number_pages(url)


def get_links(url, start_page, end_page):
    """Функция возвращает ссылки на книги определенной категории или автора
    Args:
        url (int): url категории
    Returns:
        int: количество страниц в категории
    """
    global reconnection_counter
    book_links = []

    for page in tqdm(range(start_page, end_page + 1)):
        try:
            response = requests.get(urljoin(url, str(page)))
            response.raise_for_status()
            check_for_redirect(response, DOMAIN)

            soup = BeautifulSoup(response.text, "lxml")
            links = soup.select(".d_book .bookimage a")
            book_links.append([link['href'] for link in links])

        except requests.exceptions.HTTPError:
            print(f'HTTPError. The page number {page} is not exists')

        except requests.exceptions.ConnectionError:
            if reconnection_counter == 0:
                print('Get links are failed. ConnetionError. Reconnection attempt', file=sys.stderr)
                reconnection_counter = reconnection_counter + 1
                get_links(url, page, end_page) 
            else:
                print('Get links are failed. ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                time.sleep(3)
                reconnection_counter = reconnection_counter + 1
                get_links(url, page, end_page)

    book_links = sum(book_links, [])

    return book_links


def create_parser():
    parser = argparse.ArgumentParser(
            prog = 'Parser of books from library https://tululu.org/ by category/author',
            description = '''Parser for category of books and downloading''',
            epilog = '''(c) SVA 2022 GNU licensed'''
    )
    parser.add_argument ('-p', '--path', required=True, type=str, help="Path to page of books category. For example: 'l55/', 'fantastic/', 'a8146/'")
    parser.add_argument ('-s', '--start_page', nargs='?', type=int, default=1, help="Page number for start of downloading from category. Default: 1")
    parser.add_argument ('-e', '--end_page', nargs='?', type=int, help="Page number for finish of downloading from category. Default is the last page of category. Default: start_page + 1")
    parser.add_argument ('-d', '--dest_folder', nargs='?', type=str, default="./", help="Destination folder for books and images")
    parser.add_argument ('-t', '--skip_txt', action="store_true", default=False, help="Skip donwloaind of books. Default: False")
    parser.add_argument ('-i', '--skip_imgs', action="store_true", default=False, help="Skip donwloaind of images. Default: False")
    parser.add_argument ('-j', '--json_path', nargs='?', type=str, default="./", help="Destination for json file")


    parser.add_argument ('--version',
            action='version',
            help = 'Вывести номер версии',
            version='%(prog)s {}'.format (VERSION))
 
    return parser


def main():
    global reconnection_counter
    parser = create_parser()
    args = parser.parse_args()
    url = urljoin(DOMAIN, args.path)
    npage = get_number_pages(url)
    collection = []

    if args.end_page == None:
        args.end_page = args.start_page + 1

    if args.end_page > npage or args.start_page > npage:
        args.start_page = npage
        args.end_page = npage

    if args.end_page < args.start_page or args.start_page <= 0 or args.end_page <= 0:
        print("Error. Указан некорректный диапазон страниц", file=sys.stderr)
        quit()

    book_links = get_links(url, args.start_page, args.end_page)

    for book_link in tqdm(book_links):
        success_connection = False
        while not success_connection:
            try:
                book_url = urljoin(DOMAIN, book_link)
                response = requests.get(book_url)
                reconnection_counter = 0
                success_connection = True
                book_description = parse_book_page(response.text)
                path_to_books = sanitize_filepath(os.path.join(args.dest_folder, "books", book_description["title"]))
                book_description["book_path"] = f'{path_to_books}.txt'

                book_id = re.search("\d+", book_link)[0]
                params = {"id": book_id}
                book_txt_url = f'{DOMAIN}txt.php'

                if not args.skip_txt:
                    download_txt(book_txt_url, params, book_description['title'], os.path.join(args.dest_folder, 'books'))

                if not args.skip_imgs:
                    download_image(urljoin(DOMAIN, book_description['img_src']), book_description['img_name'], os.path.join(args.dest_folder, 'img'))
                
                collection.append(book_description)

            except requests.exceptions.HTTPError:
                print(f'HTTPError. The book id {book_id} is not exists', file=sys.stderr)
                reconnection_counter = 0

            except requests.exceptions.ConnectionError:
                if reconnection_counter == 0:
                    print('Downloading of book is failed. ConnetionError. Reconnection attempt', file=sys.stderr)
                    reconnection_counter = reconnection_counter + 1
                else:
                    print('Downloading of book is failed. ConnetionError. Reconnection attempt (3 sec.)', file=sys.stderr)
                    time.sleep(3)
                    reconnection_counter = reconnection_counter + 1

    collection_json = json.dumps(collection, ensure_ascii=False, indent=4)

    with open(os.path.join(args.json_path, "books.json"), "w", encoding='utf8') as books:
        books.write(collection_json)


if __name__ == "__main__":
    main()