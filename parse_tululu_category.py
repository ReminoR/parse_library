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


def download_category(url_category, start_page, end_page, dest_folder="./", skip_txt=False, skip_imgs=False, json_path="./"):
    """Функция для скачивания категорий книг.
    Args:
        category_number (int): id категории, которую собираетесь скачать
        start_page (int): начиная с какой страницы скачивать книги
        end_page (int): заканчивая какой страницей скачивать книги 
        books_folder (str): Папка, куда сохранять книги
        skip_txt (bool): не скачивать книги
        images_folder (str): Папка, куда сохранять обложки книг
        skip_imgs (bool): не скачивать картинки
        json_path (str): указать путь для json файла
    Returns:
        str: ссылки на скаченные книги
    """

    books_info = []
    os.makedirs(json_path, exist_ok=True)

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
                book_info["book_path"] = f'{sanitize_filepath(os.path.join(dest_folder, "books", sanitize_filename(book_info["title"])))}.txt'
                params = {"id": book_id}
                book_url_txt = f'{DOMAIN}txt.php'

                if not skip_txt:
                    download_txt(book_url_txt, params, book_info['title'], os.path.join(dest_folder, 'books'))

                if not skip_imgs:
                    download_image(urljoin(DOMAIN, book_info['img_src']), book_info['img_name'], os.path.join(dest_folder, 'img'))
                books_info.append(book_info)

            except requests.exceptions.HTTPError:
                print(f'HTTPError. The book id {book_id} is not exists')


            book_info_json = json.dumps(books_info, ensure_ascii=False, indent=4)
            with open(os.path.join(json_path, "books.json"), "w", encoding='utf8') as books:
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
    parser.add_argument ('-s', '--start_page', nargs='?', type=int, default=1, help="Page number for start of downloading from category")
    parser.add_argument ('-e', '--end_page', nargs='?', type=int, default=None, help="Page number for finish of downloading from category")
    parser.add_argument ('-d', '--dest_folder', nargs='?', type=str, default="./", help="Destination folder for books and images")
    parser.add_argument ('-t', '--skip_txt', action="store_true", default=False, help="Skip donwloaind of books")
    parser.add_argument ('-i', '--skip_imgs', action="store_true", default=False, help="Skip donwloaind of images")
    parser.add_argument ('-j', '--json_path', nargs='?', type=str, default="./", help="Destination for json file")


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

    download_category(url, args.start_page, args.end_page, dest_folder = args.dest_folder, skip_txt=args.skip_txt, skip_imgs=args.skip_imgs, json_path=args.json_path)

if __name__ == "__main__":
    main()