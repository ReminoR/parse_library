import re
import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathvalidate import sanitize_filename, sanitize_filepath
from tululu import download_txt, parse_book_page, download_image, check_for_redirect


DOMAIN = "https://tululu.org/"


def download_category(category_number, start_page, end_page, books_folder='./books/', images_folder="./img"):
    url_category = f"https://tululu.org/l{category_number}/"
    books_info = []

    for page in range(start_page, end_page):
        response = requests.get(urljoin(url_category, str(page)))
        response.raise_for_status()
        check_for_redirect(response, DOMAIN)

        soup = BeautifulSoup(response.text, "lxml")
        books_html = soup.find_all(class_="d_book")

        for book_html in books_html:
            book_href = book_html.find("a")["href"]
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


            except requests.exceptions.HTTPError:
                print(f'HTTPError. The book id {book_id} is not exists')


            book_info_json = json.dumps(books_info, ensure_ascii=False, indent=4)
            with open("books.json", "w", encoding='utf8') as books:
                books.write(book_info_json)


def main():
    download_category(55, 1, 2)

if __name__ == "__main__":
    main()